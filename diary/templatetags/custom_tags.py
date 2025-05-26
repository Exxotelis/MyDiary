from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.simple_tag
def get_answer(answers, key, default="Δεν έχει απαντηθεί ακόμα 😶"):
    obj = answers.get(key)
    if not obj or not obj.answer:
        return default
    return obj.answer
