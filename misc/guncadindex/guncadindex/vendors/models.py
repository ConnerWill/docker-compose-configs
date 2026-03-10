from django.db import models
from django.db.models import Q
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin


class VendorManager(models.query.QuerySet):
    def annotate_visible(self):
        return self.annotate(
            visible=(Q(disabled=False) & Q(valid_after__lte=timezone.now()))
        )

    def visible(self):
        return self.annotate_visible().filter(visible=True)

    def footer(self):
        return self.visible().filter(footer=True).order_by("slug")

    def markup(self):
        return self.visible().exclude(should_markup=False)


class Vendor(ExportModelOperationsMixin("vendor"), models.Model):
    objects = VendorManager().as_manager()
    disabled = models.BooleanField(
        default=False,
        help_text="Should this vendor be hidden? Hidden vendors are not shown at all in the Index.",
    )
    valid_after = models.DateTimeField(
        default=timezone.now,
        help_text="The date and time this sponsored vendor should be shown after",
    )
    footer = models.BooleanField(
        default=False,
        verbose_name="show in footer",
        help_text="Should this vendor be shown on every page in the footer of the website?",
    )
    should_markup = models.BooleanField(
        default=False,
        help_text="NYI. Determines whether links to this vendor in descriptions of posts should be marked up richly in release detail views.",
    )
    slug = models.SlugField(
        primary_key=True,
        max_length=128,
        db_index=True,
        help_text="A unique identifier for this vendor",
    )
    logo = models.ImageField(
        upload_to="vendor_logos/",
        blank=True,
        null=True,
        help_text="A logo for this vendor. Will be displayed in several places throughout the site at a moderate size",
    )
    name = models.CharField(
        max_length=256,
        unique=True,
        help_text='The friendly name of this vendor (ex. "Velocity Arms")',
    )
    referralcode = models.CharField(
        max_length=256,
        blank=True,
        help_text="A referral code, if provided",
    )
    description = models.TextField(
        help_text="A user-facing description of this vendor. Should include a brief synopsis of who they are and the services they offer."
    )
    homepage = models.URLField(
        help_text="Where the user should be directed to if they click this vendor in the vendor list."
    )
    domains = models.CharField(
        blank=True,
        max_length=1024,
        help_text="A semicolon-separated (;) list of domains (not to be confused with URLs) this vendor is responsible for.",
    )

    class Meta:
        verbose_name = "sponsored vendor"
        verbose_name_plural = "sponsored vendors"
