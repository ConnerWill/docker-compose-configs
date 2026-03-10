# Adding Channels

## Preseeding

Upon installation, your Index should pre-seed itself with a bunch of known-good channels defined in a CSV in the root of the repo. Afterward, it will automatically discover new channels with the `guncad` or `3d2a` tags as well as try to find other channels with GunCAD content based on some special heuristics.

You shouldn't have to add channels manually, generally.

## Adding Manually

If you *really* have to, adding channels is pretty easy via the administrator's dashboard:

1. Log into the admin dash. If you haven't made an administrative user yet, see [`adding-admin.md`](./adding-admin)

2. Under "ODYSEESCRAPER", navigate to the "Odysee channels" link and click it

3. Search for and verify that the channel you wish to add isn't already present

4. Click "ADD ODYSEE CHANNEL" in the top-right

5. Populate the information it asks for and hit "Save"

## Notes

A few things to note:

* The name is the human readable name of the channel and should match what's on Odysee (unless you need to censor/redact/correct it)

* The description is NOT user-facing

* The handle must NOT be the URL. It should be just the handle (ex. `@blazbobabbins:f2`)

The next time GunCAD Index scrapes for content, it will acquire content from that channel. If you'd like to trigger a scrape ahead of time, see [`manual-scrape.md`](./manual-scrape.md)
