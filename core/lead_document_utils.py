"""Shared helpers for listing lead files in portals."""

import json


def lead_files_payload(lead):
    """Build document list: service ZIP, extracted ZIP files, follow-up uploads."""
    items = []
    if lead.service_documents_zip:
        service_name = lead.service.name if lead.service_id else "Service"
        items.append(
            {
                "label": f"{service_name} documents (ZIP)",
                "url": lead.service_documents_zip.url,
                "date": lead.updated_at.strftime("%d %b %Y") if lead.updated_at else "",
                "type": "ZIP archive",
            }
        )
    for doc in lead.extracted_documents.all():
        items.append(
            {
                "label": doc.original_name,
                "url": doc.file.url if doc.file else "",
                "date": doc.created_at.strftime("%d %b %Y") if doc.created_at else "",
                "type": "From staff ZIP",
            }
        )
    for doc in lead.documents.all():
        items.append(
            {
                "label": doc.display_name,
                "url": doc.file.url if doc.file else "",
                "date": doc.created_at.strftime("%d %b %Y") if doc.created_at else "",
                "type": doc.get_doc_type_display(),
            }
        )
    return items


def lead_files_json(lead):
    return json.dumps(lead_files_payload(lead))


def lead_detail_payload(lead):
    """All lead fields for follow-up / back office detail view."""
    return {
        "id": lead.display_id,
        "name": lead.name,
        "phone": lead.phone or "",
        "email": lead.email or "",
        "type": lead.get_company_display(),
        "service": lead.service.name if lead.service_id else "",
        "source": lead.source.name if lead.source_id else "",
        "branch": lead.branch.name if lead.branch_id else "",
        "staff": lead.created_by.get_username() if lead.created_by_id else "",
        "status": lead.followup_status.name if lead.followup_status_id else "",
        "staff_status": lead.staff_status.name if lead.staff_status_id else "",
        "followup_status": lead.followup_status.name if lead.followup_status_id else "",
        "takhlees_id": lead.takhlees_id or "",
        "passport_no": lead.passport_no or "",
        "eid_no": lead.eid_no or "",
        "notes": lead.notes or "",
        "doc_notes": lead.doc_collection_notes or "",
        "next_followup": lead.next_followup_date.strftime("%d %b %Y") if lead.next_followup_date else "",
        "service_expire": lead.service_expire_date.strftime("%d %b %Y") if lead.service_expire_date else "",
        "sent_to_followup": lead.sent_to_followup_at.strftime("%d %b %Y %H:%M") if lead.sent_to_followup_at else "",
        "zip_url": lead.service_documents_zip.url if lead.service_documents_zip else "",
        "zip_label": f"{lead.service.name} documents (ZIP)" if lead.service_id and lead.service_documents_zip else "Service documents (ZIP)",
        "doc_passport": lead.doc_passport_collected,
        "doc_certs": lead.doc_certificates_collected,
        "doc_photos": lead.doc_photos_collected,
        "files": lead_files_payload(lead),
    }


def lead_zip_check_payload(lead):
    """Staff ZIP files for follow-up check modal."""
    files = []
    for doc in lead.extracted_documents.all():
        files.append(
            {
                "id": doc.pk,
                "name": doc.original_name,
                "url": doc.file.url if doc.file else "",
                "checked": doc.followup_checked,
            }
        )
    return {
        "zip_url": lead.service_documents_zip.url if lead.service_documents_zip else "",
        "zip_label": f"{lead.service.name} documents (ZIP)" if lead.service_id else "Service documents (ZIP)",
        "zip_verified": lead.service_zip_verified,
        "files": files,
    }


def lead_zip_check_json(lead):
    return json.dumps(lead_zip_check_payload(lead))


def lead_detail_json(lead):
    return json.dumps(lead_detail_payload(lead))
