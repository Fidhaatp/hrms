"""Helpers for opening and updating client cases."""

from core.models import ClientCase, Lead


def ensure_client_case(lead, user, *, service_type=None):
    """Open a processing case for a customer (after follow-up document work)."""
    service_type = service_type or ClientCase.ServiceType.ADMISSION
    case, created = ClientCase.objects.get_or_create(
        lead=lead,
        defaults={
            "branch": lead.branch,
            "client_name": lead.name,
            "status": ClientCase.ProcessingStage.OPENED,
            "service_type": service_type,
            "assigned_to": user,
            "processed_by": user,
        },
    )
    if created:
        case.log_processing(
            user,
            note="Case opened — follow-up handed customer to back office for processing.",
            stage=ClientCase.ProcessingStage.OPENED,
        )
    return case, created


def lead_documents_summary(lead):
    items = []
    if lead.doc_passport_collected:
        items.append("Passport")
    if lead.doc_certificates_collected:
        items.append("Certificates")
    if lead.doc_photos_collected:
        items.append("Photos")
    return items
