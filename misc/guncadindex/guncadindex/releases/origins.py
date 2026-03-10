import logging
import pprint
from datetime import datetime, timezone

from django.db import transaction

from . import lbry, models

logger = logging.getLogger(__name__)


# TO ADD:
#  * Thingiverse
#  * Printables
#  * Makerworld
#  * Torrent
#  * IPFS
class Origin:
    download_links = [
        {
            "name": "Unknown Link",
            "desc": "Please submit a bug report",
            "build_link": lambda origin: f"{origin}",
        }
    ]

    def __str__(self):
        return str(type(self))

    def _add_release(self, **kwargs):
        channel = kwargs.get("channel")
        release_id = kwargs.get("release_id")
        release = kwargs.get("release")
        choice = models.Origin.get_origin_choice(self) or -1
        link = kwargs.get("link")
        with transaction.atomic():
            r, rcreated = models.Release.objects.update_or_create(
                id=release_id, defaults=release
            )
            d, dcreated = models.ReleaseDownloadMethod.objects.update_or_create(
                release=r,
                origin=choice,
                defaults={"link": link},
            )

    def _update_release(self, **kwargs):
        # TODO: Update the linked release
        release = kwargs.get("release")
        logger.warn(f"NYI _update_release {self} - {release}")
        return False

    def _update_channel(self, **kwargs):
        # TODO: Update the linked channel
        channel = kwargs.get("channel")
        logger.warn(f"NYI _update_channel {self} - {channel}")
        return False

    def discover(self, **kwargs):
        # TODO: Find "new content", whatever form that takes
        logger.warn(f"NYI discover {self}")
        return False

    def get_links(self, origin):
        return [
            {**entry, "link": entry["build_link"](origin)}
            for entry in self.download_links
        ]

    def update(self, **kwargs):
        if not "origin" in kwargs:
            return False
        if "release" in kwargs:
            return self._update_release(**kwargs)
        elif "channel" in kwargs:
            return self._update_channel(**kwargs)


class ManualOrigin(Origin):
    download_links = [
        {
            "name": "Download",
            "desc": "Download this release directly",
            "build_link": lambda origin: f"{origin}",
        }
    ]

    def _update_release(self, **kwargs):
        # ManualOrigin should not have substantial updates for manually-added releases
        return

    def _update_channel(self, **kwargs):
        # ManualOrigin should not have substantial updates for manually-added channels
        return

    def discover(self, **kwargs):
        # ManualOrigin should not be able to discover content
        return


class LbryOrigin(Origin):
    download_links = [
        {
            "name": "LBRY",
            "desc": "View this release using LBRY Desktop",
            "build_link": lambda origin: f"{origin}",
        }
    ]
    download_link_name = "LBRY"
    download_link_desc = "View this release using LBRY Desktop"

    def _update_channel(self, channel, link, **kwargs):
        # Take a channel and fetch all of its stream claims, adding
        # and/or updating releases
        assert channel
        assert link
        claims = lbry.claim_search(link)
        for claimid, claimdata in claims.items():
            try:
                print = pprint.pp
                # print(claimid)
                # print(claimdata)
                value = claimdata.get("value", {})
                self._add_release(
                    channel=channel,
                    release_id=claimid,
                    release={
                        "name": value.get("title"),
                        "description": value.get("description"),
                        "channel": channel,
                        "released": datetime.fromtimestamp(
                            int(value.get("release_time")), tz=timezone.utc
                        ),
                    },
                    link=claimdata.get("short_url").replace("#", ":"),
                )
            except Exception as e:
                logger.warn(f"Could not make Release for claim {claimid}: {e}")

    def discover(self, **kwargs):
        lbry.wait_for_component("wallet")
        return
