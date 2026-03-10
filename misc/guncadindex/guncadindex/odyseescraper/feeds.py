from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed

from .models import OdyseeRelease

DESCRIPTION_TEMPLATE = """
By: {release.channel.name} ({release.channel.handle})
Size: {release.size_friendly}
{release.tag_list}

{release.description}
"""


class OdyseeReleaseRSSFeed(Feed):
    link = "/search/"
    allowed_sorts = ["newest", "updated"]

    def get_object(self, request):
        self.query = request.GET.get("query", "")
        sort = request.GET.get("sort", "newest")
        self.sort = sort if sort in self.allowed_sorts else self.allowed_sorts[0]
        self.tags = request.GET.getlist("tag", [])
        if self.query:
            # We have a search query, and that's the most important part
            self.formatted_title = f"GunCAD Index - '{self.query}'"
            self.formatted_description = (
                f"Just the results for your search query: {self.query}"
            )
        elif self.tags:
            # We have some tags to the user provided, so show those
            tags = ", ".join(self.tags)
            self.formatted_title = f"GunCAD Index - {tags}"
            self.formatted_description = f"Just the results for your tag search: {tags}"
        elif self.sort == "updated":
            # User's got a feed that's just updates
            self.formatted_title = "GunCAD Index - Updates"
            self.formatted_description = (
                "Only releases that were posted and then later updated"
            )
        else:
            # No params = default title/desc
            self.formatted_title = "GunCAD Index"
            self.formatted_description = (
                "Everything the GunCAD Index has on offer, straight from the firehose."
            )
        return None

    def title(self):
        return self.formatted_title

    def description(self):
        return self.formatted_description

    def items(self):
        if self.sort == "random":
            return OdyseeRelease.objects.none()
        else:
            return OdyseeRelease.objects.search(
                query=self.query,
                sort=self.sort,
                tags=self.tags,
            )[:25]

    def feed_updated(self):
        latest = self.get_object(self.request).order_by("-last_updated").first()
        if latest:
            return latest.last_updated
        return timezone.now()

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return DESCRIPTION_TEMPLATE.format(release=item)

    def item_link(self, item):
        return reverse("detail", args=[item.slug])

    def item_guid(self, item):
        return item.id

    def item_updated(self, item):
        return item.last_updated or item.released

    def item_enclosure_url(self, item):
        return item.thumbnail_small

    def item_enclosure_mime_type(self, item):
        return "image/webp"


class OdyseeReleaseAtomFeed(OdyseeReleaseRSSFeed):
    feed_type = Atom1Feed
    subtitle = OdyseeReleaseRSSFeed.description
