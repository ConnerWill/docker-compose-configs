from django.contrib.auth.models import Group, User
from odyseescraper.models import OdyseeChannel, OdyseeRelease, Tag, TaggingRule
from releases.serializers import ThumbnailSerializer
from rest_framework import serializers


class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "slug", "name", "description", "color", "text_color"]


class TaggingRuleSerializer(serializers.HyperlinkedModelSerializer):
    required_tag = TagSerializer(read_only=True)
    tag = TagSerializer(read_only=True)

    class Meta:
        model = TaggingRule
        fields = [
            "id",
            "name",
            "title_regex",
            "description_regex",
            "channel_regex",
            "required_tag",
            "tag",
        ]


class OdyseeChannelSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_manager = ThumbnailSerializer(read_only=True)

    def get_url(self, obj):
        return obj.url

    class Meta:
        model = OdyseeChannel
        fields = [
            "id",
            "claimid",
            "name",
            "handle",
            "thumbnail_manager",
            "url",
            "lbry_only",
        ]


class OdyseeReleaseSerializer(serializers.HyperlinkedModelSerializer):
    channel = OdyseeChannelSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    thumbnail_manager = ThumbnailSerializer(read_only=True)

    class Meta:
        model = OdyseeRelease
        fields = [
            "id",
            "shortlink",
            "name",
            "description",
            "odysee_views",
            "odysee_likes",
            "odysee_dislikes",
            "url",
            "url_lbry",
            "channel",
            "discovered",
            "released",
            "last_updated",
            "thumbnail",
            "thumbnail_manager",
            "size",
            "sd_hash",
            "sha384sum",
            "lbry_only",
            "canonical_release_state",
            "tags",
            "duplicate",
        ]
