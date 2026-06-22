import json

from django import template
from django.utils.safestring import mark_safe

from core.lead_document_utils import lead_detail_json as build_lead_detail_json
from core.lead_document_utils import lead_files_json as build_lead_files_json
from core.lead_document_utils import lead_zip_check_json as build_lead_zip_check_json

register = template.Library()


@register.filter
def lead_documents_json(lead):
    """JSON list of all lead files for view modal."""
    return build_lead_files_json(lead)


@register.filter
def lead_detail_json(lead):
    """JSON of all lead fields for detail modal."""
    return build_lead_detail_json(lead)


@register.filter
def lead_zip_check_json(lead):
    """JSON of staff ZIP files for follow-up check modal."""
    return build_lead_zip_check_json(lead)


@register.filter
def staff_status_history_json(lead):
    """JSON history for staff status change modal."""
    return mark_safe(json.dumps(lead.staff_status_history_payload()))


@register.filter
def lead_procedure_steps_json(lead):
    """JSON procedure steps for follow-up/back office modal."""
    return mark_safe(json.dumps(lead.procedure_steps_payload()))


@register.filter
def lead_phone_country(lead):
    from core.phone_validation import split_stored_lead_phone

    return split_stored_lead_phone(lead.phone)[0]


@register.filter
def lead_phone_national(lead):
    from core.phone_validation import split_stored_lead_phone

    return split_stored_lead_phone(lead.phone)[1]
