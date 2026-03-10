from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("odyseescraper", "0091_alter_odyseerelease_popularity"),
    ]

    operations = [
        TrigramExtension(),
    ]
