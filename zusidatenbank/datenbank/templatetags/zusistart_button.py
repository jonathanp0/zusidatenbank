import datetime
from django import template

register = template.Library()


@register.inclusion_tag("include/zusistart_button.html")
def zusistart_button(fpn_path, zug_nummer, mini):
    encodedpath = fpn_path.replace("\\", "?")

    return {"fpn": encodedpath, "nummer": zug_nummer, "mini": mini}
