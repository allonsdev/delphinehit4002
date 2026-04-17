import json
from django import template

register = template.Library()

@register.filter
def parse_json_list(value):
    try:
        return json.loads(value)
    except:
        return []