"""Lead service ZIP upload handling and extraction."""

import zipfile
from pathlib import Path, PurePosixPath

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from core.models import Lead, LeadExtractedDocument, LeadService

LEAD_SERVICE_ZIP_FIELD = "lead_service_zip"
MAX_EXTRACTED_FILES = 50
MAX_EXTRACTED_FILE_BYTES = 10 * 1024 * 1024


def get_active_lead_services():
    return LeadService.objects.filter(is_active=True).order_by("sort_order", "name")


def validate_lead_service_zip(files):
    uploaded = files.get(LEAD_SERVICE_ZIP_FIELD) if files is not None else None
    if not uploaded:
        raise ValidationError("Service documents ZIP file is required.")
    if not uploaded.name.lower().endswith(".zip"):
        raise ValidationError("Upload a ZIP file containing all service documents.")


def _safe_zip_member_name(name):
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        return None
    filename = path.name
    if not filename or filename.startswith("."):
        return None
    return filename


def extract_lead_service_zip(lead):
    """Extract ZIP contents so follow-up can view individual files."""
    if not lead.service_documents_zip:
        lead.extracted_documents.all().delete()
        return []

    lead.extracted_documents.all().delete()
    saved = []
    try:
        with zipfile.ZipFile(lead.service_documents_zip.path, "r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if len(saved) >= MAX_EXTRACTED_FILES:
                    break
                if info.file_size > MAX_EXTRACTED_FILE_BYTES:
                    continue
                filename = _safe_zip_member_name(info.filename)
                if not filename:
                    continue
                data = archive.read(info)
                if not data:
                    continue
                obj = LeadExtractedDocument(lead=lead, original_name=filename)
                obj.file.save(filename, ContentFile(data), save=True)
                saved.append(obj)
    except (zipfile.BadZipFile, OSError, ValueError):
        return saved
    return saved


def save_lead_service_zip(lead, files):
    uploaded = files.get(LEAD_SERVICE_ZIP_FIELD) if files is not None else None
    if not uploaded:
        return lead
    lead.service_documents_zip = uploaded
    lead.service_zip_verified = False
    lead.save(update_fields=["service_documents_zip", "service_zip_verified", "updated_at"])
    extract_lead_service_zip(lead)
    return lead
