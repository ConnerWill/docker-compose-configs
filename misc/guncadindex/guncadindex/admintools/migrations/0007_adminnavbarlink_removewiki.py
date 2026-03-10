from django.db import migrations


def update_wiki_link(apps, schema_editor):
    NavbarLink = apps.get_model("admintools", "AdminNavbarLink")

    NavbarLink.objects.filter(id="000-wiki").update(
        link="https://wiki.guncadindex.com", newtab=True
    )


class Migration(migrations.Migration):
    dependencies = [
        ("admintools", "0006_adminnavbarlink_datapopulation"),
    ]

    operations = [
        migrations.RunPython(update_wiki_link, migrations.RunPython.noop),
    ]
