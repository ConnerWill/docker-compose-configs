import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.urls import NoReverseMatch, reverse
from django_prometheus.models import ExportModelOperationsMixin


class AdminSiteBannerManager(models.query.QuerySet):
    def visible(self):
        return self.filter(visible=True).order_by("-priority", "id")


class AdminSiteBanner(ExportModelOperationsMixin("banner"), models.Model):
    """
    A site-wide banner. All visible banners will be displayed at the same time
    """

    class Meta:
        verbose_name = "sitewide banner"
        verbose_name_plural = "sitewide banners"

    objects = AdminSiteBannerManager().as_manager()
    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this banner",
    )
    priority = models.IntegerField(
        default=1000,
        db_index=True,
        help_text="Higher numbers are higher up in the list of sitewide banners",
    )
    visible = models.BooleanField(
        default=False, help_text="Should this banner be visible below the navbar?"
    )
    text = models.TextField(
        help_text="The contents of the text of this banner. Can contain HTML"
    )
    color = models.CharField(
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                #                        v How many bytes per channel (locked to 2)
                #                            v How many channels total (RGB or RGBA)
                regex=r"^#(?:[0-9a-fA-F]{2}){3,4}$",
                message='Field must be a valid hex RGB color code prepended with "#"',
                code="invalid",
            )
        ],
        help_text="The RGB hex code (with #) of the color of the banner. If unspecified, a default will be chosen",
    )

    @property
    def text_color(self):
        if not self.color:
            return ""
        # https://nemecek.be/blog/172/how-to-calculate-contrast-color-in-python
        color = self.color[1:]
        hex_red = int(color[0:2], base=16)
        hex_green = int(color[2:4], base=16)
        hex_blue = int(color[4:6], base=16)
        luminance = hex_red * 0.2126 + hex_green * 0.7152 + hex_blue * 0.0722
        if luminance < 140:
            return "rgba(255,255,255,0.95)"
        else:
            return "rgba(0,0,0,0.95)"


class AdminNavbarLinkManager(models.query.QuerySet):
    def visible(self):
        return self.filter(visible=True).order_by("-priority", "id")


class AdminNavbarLink(ExportModelOperationsMixin("navbarlink"), models.Model):
    """
    A link to put in the navbar
    """

    class Meta:
        verbose_name = "navbar link"
        verbose_name_plural = "navbar links"

    objects = AdminNavbarLinkManager().as_manager()
    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this navbar link",
    )
    priority = models.IntegerField(
        default=1000,
        db_index=True,
        help_text="Higher numbers are higher up in the list of navbar links",
    )
    visible = models.BooleanField(
        default=False, help_text="Should this link be visible in the navbar?"
    )
    newtab = models.BooleanField(
        default=False, help_text="Should this link open in a new tab?"
    )
    text = models.CharField(max_length=128, help_text="The title of this navbar")
    link = models.CharField(help_text="Where this navbar link should go to")
    css_class = models.CharField(
        max_length=256,
        blank=True,
        help_text="Any additional classes this link should have",
    )

    @property
    def destination(self):
        if self.link.startswith("url:"):
            viewname = self.link[4:]
            try:
                return reverse(viewname)
            except NoReverseMatch:
                return "url:invalid"
        return self.link
