from django.contrib.auth.models import Group, User
from releases.models import Thumbnail
from rest_framework import serializers


class ThumbnailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Thumbnail
        fields = ["small", "large", "color", "style", "origin"]
