from django import template

from core.profile_utils import get_avatar_context

register = template.Library()


@register.inclusion_tag("core/includes/profile_avatar.html")
def profile_avatar(user, size="md", extra_class=""):
    ctx = get_avatar_context(user)
    ctx["size"] = size
    ctx["extra_class"] = extra_class
    return ctx
