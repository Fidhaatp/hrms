import json

from django import template
from django.utils.html import escape

from hr.team_documents import team_document_view_items

register = template.Library()


@register.simple_tag
def team_documents_json(user, branch=None):
    """JSON list of document view links for data-documents on view buttons."""
    items = team_document_view_items(user, branch)
    if not items:
        return ""
    return escape(json.dumps(items))
