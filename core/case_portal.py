"""Back office case processing — post-sale customer work."""

from django import forms
from django.contrib import messages
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from core.backoffice_utils import backoffice_cases_queryset_for_user
from core.case_utils import ensure_client_case, lead_documents_summary
from core.models import CaseProcessingLog, ClientCase, LeadDocument, UserProfile
from core.portal import portal_role_required, render_portal_page
from core.portal_pages import backoffice_case_processing_steps, client_journey_steps

FORM_CONTROL = {"class": "form-control"}


class BackofficeCaseProcessingForm(forms.Form):
    """Record actual processing work on a customer case."""

    status = forms.ChoiceField(
        choices=ClientCase.ProcessingStage.choices,
        label="Processing stage",
        widget=forms.Select(attrs=FORM_CONTROL),
    )
    documents_verified = forms.BooleanField(
        required=False,
        label="All documents verified",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    documents_verification_note = forms.CharField(
        required=False,
        label="Document verification notes",
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
    )
    application_reference = forms.CharField(
        required=False,
        max_length=120,
        label="Application reference",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Student / application ID"}),
    )
    universities_applied = forms.CharField(
        required=False,
        label="Submitted to",
        widget=forms.Textarea(
            attrs={**FORM_CONTROL, "rows": 3, "placeholder": "Embassy, authority, or provider — one per line"}
        ),
    )
    submission_reference = forms.CharField(
        required=False,
        max_length=120,
        label="Submission reference",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Online / file reference number"}),
    )
    university_response_summary = forms.CharField(
        required=False,
        label="Authority response",
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
    )
    customer_status_update = forms.CharField(
        required=False,
        label="Customer status update",
        widget=forms.Textarea(
            attrs={**FORM_CONTROL, "rows": 2, "placeholder": "What you told the customer"}
        ),
    )
    notes = forms.CharField(
        required=False,
        label="Internal notes",
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
    )
    log_note = forms.CharField(
        required=False,
        label="Activity log entry",
        widget=forms.Textarea(
            attrs={**FORM_CONTROL, "rows": 2, "placeholder": "What you did in this step"}
        ),
    )
    completion_notes = forms.CharField(
        required=False,
        label="Case completion summary",
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
    )

    def __init__(self, case, *args, **kwargs):
        self.case = case
        super().__init__(
            *args,
            initial={
                "status": case.status,
                "documents_verified": case.documents_verified,
                "documents_verification_note": case.documents_verification_note,
                "application_reference": case.application_reference,
                "universities_applied": case.universities_applied,
                "submission_reference": case.submission_reference,
                "university_response_summary": case.university_response_summary,
                "customer_status_update": case.customer_status_update,
                "notes": case.notes,
                "completion_notes": case.completion_notes,
            },
            **kwargs,
        )

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        if status == ClientCase.ProcessingStage.DOCUMENTS_VERIFIED:
            if not cleaned.get("documents_verified") and not self.case.documents_verified:
                self.add_error(
                    "documents_verified",
                    "Confirm documents are verified before this stage.",
                )
        if status == ClientCase.ProcessingStage.PORTALS_UPLOADED:
            ref = (cleaned.get("submission_reference") or "").strip()
            if not ref and not (self.case.submission_reference or "").strip():
                self.add_error(
                    "submission_reference",
                    "Enter the submission reference.",
                )
        if status == ClientCase.ProcessingStage.COMPLETED:
            note = (cleaned.get("completion_notes") or "").strip()
            if not note and not (self.case.completion_notes or "").strip():
                self.add_error("completion_notes", "Add a completion summary.")
        return cleaned

    def save(self, user):
        data = {
            "status": self.cleaned_data["status"],
            "documents_verified": self.cleaned_data.get("documents_verified", False),
            "documents_verification_note": self.cleaned_data.get("documents_verification_note") or "",
            "application_reference": self.cleaned_data.get("application_reference") or "",
            "universities_applied": self.cleaned_data.get("universities_applied") or "",
            "submission_reference": (self.cleaned_data.get("submission_reference") or "").strip(),
            "university_response_summary": self.cleaned_data.get("university_response_summary") or "",
            "customer_status_update": self.cleaned_data.get("customer_status_update") or "",
            "notes": self.cleaned_data.get("notes") or "",
            "completion_notes": self.cleaned_data.get("completion_notes") or "",
            "log_note": self.cleaned_data.get("log_note") or "",
        }
        self.case.apply_processing_update(user, **data)
        return self.case


def _cases_queryset(user):
    from core.lead_documents import documents_prefetch

    return backoffice_cases_queryset_for_user(user).select_related(
        "lead", "branch", "assigned_to", "processed_by"
    ).prefetch_related(
        Prefetch("processing_logs", queryset=CaseProcessingLog.objects.select_related("created_by")),
        Prefetch("lead__documents", queryset=LeadDocument.objects.select_related("uploaded_by")),
    ).order_by("-updated_at")


def _status_counts(user):
    qs = backoffice_cases_queryset_for_user(user)
    counts = {row["status"]: row["c"] for row in qs.values("status").annotate(c=Count("id"))}
    stages = ClientCase.ProcessingStage
    return {
        "all": qs.count(),
        "opened": counts.get(stages.OPENED, 0),
        "documents_verified": counts.get(stages.DOCUMENTS_VERIFIED, 0),
        "application_created": counts.get(stages.APPLICATION_CREATED, 0),
        "applied_universities": counts.get(stages.APPLIED_UNIVERSITIES, 0),
        "portals_uploaded": counts.get(stages.PORTALS_UPLOADED, 0),
        "tracking_responses": counts.get(stages.TRACKING_RESPONSES, 0),
        "customer_updated": counts.get(stages.CUSTOMER_UPDATED, 0),
        "completed": counts.get(stages.COMPLETED, 0),
    }


def _filter_cases(user, status_filter):
    qs = _cases_queryset(user)
    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)
    return qs[:200]


def _case_context_base(user, **extra):
    defaults = {
        "status_counts": _status_counts(user),
        "processing_steps": backoffice_case_processing_steps(),
        "journey_steps": client_journey_steps(),
        "status_choices": ClientCase.ProcessingStage.choices,
    }
    defaults.update(extra)
    return defaults


def backoffice_cases_list_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    def view(request):
        status_filter = request.GET.get("status", "all")
        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/cases/backoffice_list.html",
            "Case Processing",
            active_nav="cases",
            **_case_context_base(
                request.user,
                status_filter=status_filter,
                cases=_filter_cases(request.user, status_filter),
            ),
        )

    return view


def _stage_progress(case):
    order = case.processing_stage_order()
    try:
        idx = order.index(case.status)
    except ValueError:
        idx = 0
    items = []
    for key, label in ClientCase.ProcessingStage.choices:
        if key == ClientCase.ProcessingStage.OPENED:
            continue
        key_idx = order.index(key)
        if key_idx < idx:
            state = "done"
        elif key_idx == idx:
            state = "current"
        else:
            state = "pending"
        items.append({"key": key, "label": label, "state": state})
    return items


def backoffice_case_detail_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    def view(request, pk):
        case = get_object_or_404(_cases_queryset(request.user), pk=pk)
        lead = case.lead
        doc_items = lead_documents_summary(lead) if lead else []
        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/cases/case_detail.html",
            f"Process {case.case_ref}",
            active_nav="cases",
            **_case_context_base(
                request.user,
                case=case,
                lead=lead,
                doc_items=doc_items,
                stage_progress=_stage_progress(case),
                logs=case.processing_logs.all()[:30],
                case_form=BackofficeCaseProcessingForm(case),
            ),
        )

    return view


def backoffice_case_update_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @require_http_methods(["POST"])
    def view(request, pk):
        case = get_object_or_404(_cases_queryset(request.user), pk=pk)
        form = BackofficeCaseProcessingForm(case, request.POST)
        status_filter = request.POST.get("status_filter", "all")
        detail_redirect = request.POST.get("detail", "") == "1"

        if form.is_valid():
            form.save(request.user)
            messages.success(
                request,
                f"{case.case_ref} — now at «{case.get_status_display()}».",
            )
            if detail_redirect:
                return redirect("backoffice:case_detail", pk=case.pk)
            base = reverse("backoffice:cases")
            if status_filter and status_filter != "all":
                return redirect(f"{base}?status={status_filter}")
            return redirect(base)

        if detail_redirect:
            lead = case.lead
            return render_portal_page(
                request,
                UserProfile.UserType.BACKOFFICE,
                "portal/cases/case_detail.html",
                f"Process {case.case_ref}",
                active_nav="cases",
                **_case_context_base(
                    request.user,
                    case=case,
                    lead=lead,
                    doc_items=lead_documents_summary(lead) if lead else [],
                    stage_progress=_stage_progress(case),
                    logs=case.processing_logs.all()[:30],
                    case_form=form,
                ),
            )

        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/cases/backoffice_list.html",
            "Case Processing",
            active_nav="cases",
            **_case_context_base(
                request.user,
                status_filter=status_filter,
                cases=_filter_cases(request.user, status_filter),
                edit_case=case,
                case_form=form,
                show_case_modal=True,
            ),
        )

    return view


def recent_cases_for_dashboard(user, limit=8):
    return _cases_queryset(user)[:limit]
