from django import template

from formapp.models import reestr, reestInfo, files

register = template.Library()

@register.simple_tag()
def get_verbose_field_name(field):
    return reestr._meta.get_field(field).verbose_name

@register.simple_tag()
def get_verbose_field_name2(field):
    return reestInfo._meta.get_field(field).verbose_name

