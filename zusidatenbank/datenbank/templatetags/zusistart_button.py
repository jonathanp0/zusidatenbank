import datetime
from django import template

register = template.Library()

@register.inclusion_tag("include/zusistart_button.html")
def zusistart_button(show, fpn_path, zug_nummer, mini):
    encodedpath = fpn_path.replace("\\", "?")

    return {"show": show, "fpn": encodedpath, "nummer": zug_nummer, "mini": mini}
