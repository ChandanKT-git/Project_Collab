"""Template tags for mention highlighting."""
from django import template
from django.utils.safestring import mark_safe
from apps.notifications.services import MentionParser

register = template.Library()


@register.filter(name='highlight_mentions')
def highlight_mentions(text):
    """
    Template filter to highlight @username mentions in text.
    
    Usage: {{ comment.content|highlight_mentions }}
    """
    if not text:
        return text
    
    highlighted = MentionParser.highlight_mentions(text)
    return mark_safe(highlighted)
