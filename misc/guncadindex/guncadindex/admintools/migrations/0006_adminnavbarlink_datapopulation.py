from django.db import migrations


def seed_navbar_links(apps, schema_editor):
    NavbarLink = apps.get_model("admintools", "AdminNavbarLink")
    defaults = [
        {
            "id": "000-home",
            "text": "Home",
            "link": "url:landing",
            "priority": 10000,
            "visible": True,
        },
        {
            "id": "000-browse",
            "text": "Browse",
            "link": "url:listreleases",
            "priority": 9000,
            "visible": True,
        },
        {
            "id": "000-discover",
            "text": "Discover",
            "link": "url:discover",
            "priority": 8000,
            "visible": True,
        },
        {
            "id": "000-learn",
            "text": "Learn",
            "link": "https://guide.ctrlpew.com/",
            "priority": 7000,
            "visible": True,
            "newtab": True,
        },
        {
            "id": "000-wiki",
            "text": "Wiki",
            "link": "url:wiki:root",
            "priority": 6000,
            "visible": True,
        },
        {
            "id": "000-about",
            "text": "About/FAQ",
            "link": "url:about",
            "priority": 5000,
            "visible": True,
        },
    ]
    for entry in defaults:
        NavbarLink.objects.get_or_create(id=entry["id"], defaults=entry)


class Migration(migrations.Migration):
    dependencies = [
        ("admintools", "0005_adminnavbarlink"),
    ]
    operations = [
        migrations.RunPython(seed_navbar_links, migrations.RunPython.noop),
    ]
