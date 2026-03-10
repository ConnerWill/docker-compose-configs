#! /usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path

from scour import scour

SVG_FILE = Path("contrib/logo/guncad-index.svg")
OUTPUT_DIR = Path("static/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define desired sizes and output filenames
targets = [
    # Favicons
    (16, "favicon-16.png"),
    (32, "favicon-32.png"),
    (48, "favicon-48.png"),
    # Web manifest, mostly
    (32, "icon-32x32.png"),
    (192, "icon-192x192.png"),
    (512, "icon-512x512.png"),
    # https://gitlab.com/inkscape/inkscape/-/issues/3156
    # :agony:
    (1024, "icon-1024x1024.png"),
    (1024, "icon-1024x1024-nobg.png"),
    # And a raw SVG for places we can use it
    (256, "icon.svg"),
]


def render_svg(size, filename):
    output_file = OUTPUT_DIR / filename
    inkscape_args = [
        "inkscape",
        str(SVG_FILE),
        "--export-filename",
        str(output_file),
        "--export-plain-svg",
    ]
    if not "nobg" in filename:
        inkscape_args += [
            "--export-background=#1a1a1a",
            "--export-background-opacity=255",
        ]
    if isinstance(size, tuple):
        width, height = size
        inkscape_args += [f"--export-width={width}", f"--export-height={height}"]
    else:
        inkscape_args += [f"--export-width={size}"]
    print(inkscape_args)
    subprocess.run(inkscape_args)
    print(str(output_file))
    if str(output_file).endswith(".svg"):
        print("Scouring...")
        minify_svg(output_file)


def render_background(input_png):
    output_file = OUTPUT_DIR / "background.png"
    angle = -45
    size = 128
    color = "#1d1d1d"
    crop_size = 1024
    crop_offset = 170
    crop = f"{crop_size}x{crop_size}-{crop_offset}-{crop_offset}"
    subprocess.run(
        [
            "magick",
            OUTPUT_DIR / str(input_png),
            "-gravity",
            "center",
            "-fill",
            color,
            "-colorize",
            "100",
            "-background",
            "#1a1a1a",
            "-rotate",
            str(angle),
            "-gravity",
            "center",
            "-crop",
            crop,
            "+repage",
            "-resize",
            f"{size}x{size}",
            "-layers",
            "merge",
            str(output_file),
        ],
        check=True,
    )


def generate_scrolling_background_gif_magick(
    tile_path, output_path, tile_size=128, canvas_size=1024, seconds=10, fps=30
):
    frames = seconds * fps
    delay = int(1000 / fps)
    tile_size = 128
    tmp_dir = Path(tempfile.mkdtemp(prefix="bgframes_"))
    print("Rendering scrolling background frames...")
    for i in range(frames):
        offset = int((tile_size * i) / frames)
        out_frame = tmp_dir / f"frame-{i:05d}.png"
        crop_offset = f"+{offset}+{offset}"
        subprocess.run(
            [
                "magick",
                "-size",
                f"{canvas_size}x{canvas_size}",
                f"tile:{tile_path}",
                "-crop",
                f"{canvas_size}x{canvas_size}{crop_offset}",
                "+repage",
                "-crop",
                f"{tile_size}x{tile_size}+0+0",
                "+repage",
                str(out_frame),
            ],
            check=True,
        )
    print("Assembling...")
    subprocess.run(
        f"magick -delay {delay // 10} -loop 0 {tmp_dir}/frame-*.png -layers Optimize {output_path}",
        shell=True,
        check=True,
    )

    # Clean up tmpdir
    for f in tmp_dir.glob("*.png"):
        f.unlink()
    tmp_dir.rmdir()


def minify_svg(svg_path: Path):
    options = scour.sanitizeOptions()
    options.remove_metadata = True
    options.remove_descriptive_elements = True
    options.strip_comments = True
    options.shorten_ids = True
    options.indent_type = None
    options.enable_viewboxing = True
    options.keep_editor_data = False
    options.quiet = True

    with open(svg_path, "r", encoding="utf-8") as fin:
        svg_data = fin.read()

    minified_svg = scour.scourString(svg_data, options)

    with open(svg_path, "w", encoding="utf-8") as fout:
        fout.write(minified_svg)


# Convert all target sizes
for size, name in targets:
    render_svg(size, name)

# Create our 45-deg tiled background
render_background(input_png="icon-1024x1024-nobg.png")

# Rasterize it to GIF
generate_scrolling_background_gif_magick(
    tile_path=OUTPUT_DIR / "background.png", output_path=OUTPUT_DIR / "background.gif"
)

# Generate a favicon.ico from the PNGs
subprocess.run(
    [
        "magick",
        str(OUTPUT_DIR / "favicon-16.png"),
        str(OUTPUT_DIR / "favicon-32.png"),
        str(OUTPUT_DIR / "favicon-48.png"),
        str(OUTPUT_DIR / "favicon.ico"),
    ]
)

print("Done!")
