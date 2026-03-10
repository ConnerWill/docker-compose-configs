from django import template
from django.urls import reverse
from out import utils

register = template.Library()


@register.filter
def outify(url):
    token = utils.store_outbound_url(url)
    return f"{reverse('out')}?t={token}"
