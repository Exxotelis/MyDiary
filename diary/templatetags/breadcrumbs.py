from django import template
from django.urls import resolve
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def render_breadcrumbs(context):
    request = context['request']
    path = request.path.strip('/').split('/')
    crumbs = []
    url = ''
    for index, part in enumerate(path):
        url += f'/{part}'
        name = part.replace('-', ' ').capitalize()
        if index < len(path) - 1:
            crumbs.append(f'<li class="breadcrumb-item"><a href="{url}/">{name}</a></li>')
        else:
            crumbs.append(f'<li class="breadcrumb-item active" aria-current="page">{name}</li>')

    home = '<li class="breadcrumb-item"><a href="/">Αρχική</a></li>'
    html = f'<nav aria-label="breadcrumb" class="bg-light py-2 px-3 mb-3 rounded-2 small">' \
           f'<ol class="breadcrumb mb-0">{home}{"".join(crumbs)}</ol></nav>'
    return mark_safe(html)
