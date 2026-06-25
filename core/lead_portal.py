from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods

from core.backoffice_utils import (
    backoffice_accessible_leads_queryset,
    backoffice_head_required,
    backoffice_pending_leads_for_user,
    backoffice_team_only_required,
    filter_backoffice_procedure_completed,
    filter_backoffice_procedure_in_progress,
    user_is_backoffice_head,
)
from core.lead_documents import _case_processing_leads_queryset, documents_prefetch
from core.lead_filters import (
    apply_lead_list_filters,
    filters_are_active,
    lead_filter_context,
    parse_lead_list_filters,
)
from core.lead_forms import (
    BackofficeProcedureReviewForm,
    BackofficeCheckForm,
    FollowupLeadForm,
    FollowupProcedureStepForm,
    FollowupLeadStatusForm,
    FollowupServiceExpireForm,
    FollowupZipCheckForm,
    StaffLeadAddForm,
    StaffLeadEditForm,
    StaffLeadStatusForm,
    StaffLeadUpdateForm,
)
from core.lead_service_utils import save_lead_service_zip
from core.phone_validation import phone_rules_for_client
from core.lead_utils import (
    apply_converted_lead_handoff,
    backoffice_all_leads_queryset,
    backoffice_pending_leads_queryset,
    followup_active_leads_queryset,
    followup_sent_leads_queryset,
    followup_team_leads_queryset,
    filter_leads_procedure_completed,
    filter_leads_procedure_in_progress,
    get_followup_queue_default_status,
    followup_status_is_converted,
    followup_status_sends_to_backoffice,
    get_active_lead_statuses,
    get_active_lost_reason_types,
    get_creator_branch,
    get_default_lead_status,
    get_followup_lead_statuses,
    get_staff_lead_statuses,
    is_staff_lost_status,
    staff_status_to_stage,
)
from core.lead_monitoring import (
    BRANCH_LEADS_PER_PAGE,
    branch_leads_queryset,
    branch_monitoring_queryset,
    monitoring_lead_cards,
    parse_monitoring_params,
)
from django.db.models import Count, Prefetch, Case, When, BooleanField, Value

from core.models import (
    ClientCase,
    Lead,
    LeadContact,
    LeadDocument,
    LeadExtractedDocument,
    LeadProcedureStep,
    LeadServiceProcedure,
    LeadStaffStatusHistory,
    UserProfile,
)
from core.portal import portal_role_required, render_portal_page

STAFF_LEAD_LIST = "staff:lead_list"
STAFF_LEAD_ADD = "staff:lead_add"
STAFF_LEAD_UPDATE = "staff:lead_update"
STAFF_LEAD_EDIT = "staff:lead_edit"
STAFF_LEAD_STATUS = "staff:lead_status"
BACKOFFICE_PENDING_LIST = "backoffice:pending_verifications"
BACKOFFICE_PROCEDURE_LIST = "backoffice:procedure_reviews"
BACKOFFICE_TEAM_PENDING_LEADS_LIST = "backoffice:pending_leads"
BACKOFFICE_ALL_LEADS_LIST = "backoffice:all_leads"
BACKOFFICE_LEADS_PER_PAGE = 15
FOLLOWUP_LEAD_LIST = "followup:lead_list"
FOLLOWUP_ALL_LEADS_LIST = "followup:all_leads"
FOLLOWUP_LEAD_UPDATE = "followup:lead_update"
FOLLOWUP_LEAD_CHECK_DOCS = "followup:lead_check_docs"
FOLLOWUP_LEAD_STATUS = "followup:lead_status"
FOLLOWUP_LEAD_EXPIRE_DATE = "followup:lead_expire_date"
FOLLOWUP_LEADS_PER_PAGE = 15
BRANCH_LEAD_LIST = "branch:lead_history"


def _staff_lead_context(request, **extra):
    staff_branch = get_creator_branch(request.user)
    filters = parse_lead_list_filters(request)
    leads = apply_lead_list_filters(
        Lead.objects.filter(Q(created_by=request.user) | Q(renewal_assigned_to=request.user, renewal_handled=False))
        .annotate(
            is_renewal_assigned=Case(
                When(renewal_assigned_to=request.user, renewal_handled=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by("-is_renewal_assigned", "-created_at")
        .select_related(
            "backoffice_checked_by", "branch", "source", "service", "staff_status", "followup_status", "lost_reason_type"
        )
        .prefetch_related(
            Prefetch(
                "staff_status_history",
                queryset=LeadStaffStatusHistory.objects.select_related(
                    "to_status", "lost_reason_type", "created_by"
                ).order_by("-created_at"),
            )
        )
        .annotate(
            call_count=Count('contacts', filter=Q(contacts__contact_type='call')),
            email_count=Count('contacts', filter=Q(contacts__contact_type='email')),
            whatsapp_count=Count('contacts', filter=Q(contacts__contact_type='whatsapp')),
        ),
        filters,
    )
    defaults = {
        "leads": leads,
        "filters_active": filters_are_active(filters),
        **lead_filter_context(filters, show_staff=True, show_followup=True, show_backoffice=True),
        "lost_reason_types": get_active_lost_reason_types(),
        "lead_form": StaffLeadAddForm(staff_branch=staff_branch),
        "lead_edit_form": StaffLeadEditForm(),
        "lead_update_form": StaffLeadUpdateForm(),
        "lead_status_form": StaffLeadStatusForm(),
        "lead_statuses": get_staff_lead_statuses(),
        "show_lead_modal": False,
        "show_lead_basic_edit_modal": False,
        "show_lead_update_modal": False,
        "show_lead_status_modal": False,
        "basic_edit_lead": None,
        "update_lead": None,
        "status_lead": None,
        "lead_add_url": STAFF_LEAD_ADD,
        "staff_branch": staff_branch,
        "lead_phone_rules": phone_rules_for_client(),
    }
    defaults.update(extra)
    return defaults


def staff_lead_list_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    def view(request):
        return render_portal_page(
            request,
            UserProfile.UserType.STAFF,
            "portal/leads/staff_list.html",
            "My Leads",
            active_nav="leads",
            **_staff_lead_context(request),
        )

    return view


def staff_lead_search_api_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["GET"])
    def view(request):
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 3:
            return JsonResponse({'results': []})
        
        # Search by name or phone
        leads = Lead.objects.filter(
            Q(name__icontains=q) | Q(phone__icontains=q)
        ).order_by('-created_at')[:10]
        
        from core.phone_validation import split_stored_lead_phone
        
        results = []
        for lead in leads:
            country_code, national_number = split_stored_lead_phone(lead.phone)
            results.append({
                'id': lead.id,
                'name': lead.name,
                'phone': national_number,
                'country': country_code,
            })
        return JsonResponse({'results': results})
    return view


def staff_lead_contact_api_view():
    import json
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["GET", "POST"])
    def view(request, pk):
        lead = get_object_or_404(Lead, pk=pk, created_by=request.user)
        if request.method == "POST":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            contact_type = data.get('contact_type')
            if contact_type not in [c[0] for c in LeadContact.ContactType.choices]:
                return JsonResponse({'error': 'Invalid contact type'}, status=400)
            
            LeadContact.objects.create(
                lead=lead,
                staff=request.user,
                contact_type=contact_type,
            )
            # Fetch updated counts
            lead_annotated = Lead.objects.annotate(
                call_count=Count('contacts', filter=Q(contacts__contact_type='call')),
                email_count=Count('contacts', filter=Q(contacts__contact_type='email')),
                whatsapp_count=Count('contacts', filter=Q(contacts__contact_type='whatsapp')),
            ).get(pk=lead.pk)
            return JsonResponse({
                'success': True,
                'counts': {
                    'call': lead_annotated.call_count,
                    'email': lead_annotated.email_count,
                    'whatsapp': lead_annotated.whatsapp_count,
                }
            })
        else:
            contacts = lead.contacts.select_related('staff').order_by('-created_at')
            history = []
            for c in contacts:
                history.append({
                    'id': c.id,
                    'type': c.contact_type,
                    'type_display': c.get_contact_type_display(),
                    'staff_name': c.staff.get_full_name() if c.staff else 'Unknown',
                    'date': c.created_at.strftime("%d %b %Y"),
                    'time': c.created_at.strftime("%I:%M %p").lstrip("0"),
                })
            return JsonResponse({'history': history})
    return view


def staff_lead_add_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["POST"])
    def view(request):
        staff_branch = get_creator_branch(request.user)
        form = StaffLeadAddForm(request.POST, staff_branch=staff_branch)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.branch = staff_branch or form.cleaned_data.get("branch")
            if not lead.branch:
                messages.error(request, "Select a branch before adding a lead.")
                return render_portal_page(
                    request,
                    UserProfile.UserType.STAFF,
                    "portal/leads/staff_list.html",
                    "My Leads",
                    active_nav="leads",
                    **_staff_lead_context(request, lead_form=form, show_lead_modal=True),
                )
            lead.save()
            if not staff_branch and lead.branch:
                profile = getattr(request.user, "staff_profile", None)
                if profile:
                    profile.branch = lead.branch
                    profile.save(update_fields=["branch", "updated_at"])
            lead.roadmap_entries.create(
                created_by=request.user,
                title="Lead registered",
                note=f"Staff added lead at {lead.branch.name} — status New.",
            )
            
            renewed_from_id = request.POST.get("renewed_from_lead_id")
            if renewed_from_id:
                try:
                    old_lead = Lead.objects.get(pk=renewed_from_id)
                    lead.renewed_from = old_lead
                    lead.save(update_fields=['renewed_from'])
                    if old_lead.renewal_assigned_to == request.user:
                        old_lead.renewal_handled = True
                        old_lead.save(update_fields=['renewal_handled', 'updated_at'])
                except Lead.DoesNotExist:
                    pass
                    
            messages.success(
                request,
                f"Lead {lead.display_id} added — use Update to add email, documents, and notes.",
            )
            return redirect(STAFF_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.STAFF,
            "portal/leads/staff_list.html",
            "My Leads",
            active_nav="leads",
            **_staff_lead_context(request, lead_form=form, show_lead_modal=True),
        )

    return view


def staff_lead_start_renewal_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["POST"])
    def view(request, pk):
        old_lead = get_object_or_404(Lead, pk=pk)
        
        # Ensure they are assigned to this renewal
        if old_lead.renewal_assigned_to != request.user:
            messages.error(request, "You are not assigned to renew this lead.")
            return redirect(STAFF_LEAD_LIST)
            
        staff_branch = get_creator_branch(request.user)
        branch = staff_branch or old_lead.branch
        
        # Clone it
        new_lead = Lead.objects.create(
            name=old_lead.name,
            phone=old_lead.phone,
            service=old_lead.service,
            branch=branch,
            created_by=request.user,
            renewed_from=old_lead,
            staff_status=get_default_lead_status(),
        )
        
        new_lead.roadmap_entries.create(
            created_by=request.user,
            title="Renewal started",
            note=f"Staff started renewal from previous lead ({old_lead.display_id}).",
        )
        
        # Mark the old lead's renewal as handled
        old_lead.renewal_handled = True
        old_lead.save(update_fields=['renewal_handled', 'updated_at'])
        
        messages.success(
            request,
            f"Fresh lead {new_lead.display_id} started for renewal! Please update documents and payment.",
        )
        return redirect(STAFF_LEAD_LIST)

    return view


def staff_lead_edit_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(Lead, pk=pk, created_by=request.user)
        if not lead.staff_can_edit_details:
            messages.error(
                request,
                f"{lead.display_id} is Converted — name, phone, and service cannot be changed.",
            )
            return redirect(STAFF_LEAD_LIST)
        form = StaffLeadEditForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save()
            lead.roadmap_entries.create(
                created_by=request.user,
                title="Lead details edited",
                note="Staff updated name, phone, or service.",
            )
            messages.success(request, f"Lead {lead.display_id} edited.")
            return redirect(STAFF_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.STAFF,
            "portal/leads/staff_list.html",
            "My Leads",
            active_nav="leads",
            **_staff_lead_context(
                request,
                basic_edit_lead=lead,
                lead_edit_form=form,
                show_lead_basic_edit_modal=True,
            ),
        )

    return view


def staff_lead_update_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(Lead, pk=pk, created_by=request.user)
        if not lead.staff_can_edit_details:
            messages.error(
                request,
                f"{lead.display_id} is Converted — details cannot be edited. Contact follow-up if changes are needed.",
            )
            return redirect(STAFF_LEAD_LIST)
        form = StaffLeadUpdateForm(request.POST, request.FILES, instance=lead)
        if form.is_valid():
            lead = form.save()
            save_lead_service_zip(lead, request.FILES)
            lead.roadmap_entries.create(
                created_by=request.user,
                title="Lead details updated",
                note="Staff updated email, type, source, documents, payment, or notes.",
            )
            messages.success(request, f"Lead {lead.display_id} updated.")
            return redirect(STAFF_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.STAFF,
            "portal/leads/staff_list.html",
            "My Leads",
            active_nav="leads",
            **_staff_lead_context(
                request,
                update_lead=lead,
                lead_update_form=form,
                show_lead_update_modal=True,
            ),
        )

    return view


def staff_lead_status_view():
    @portal_role_required(UserProfile.UserType.STAFF)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(Lead, pk=pk, created_by=request.user)
        previous_status = lead.staff_status
        previous_status_name = previous_status.name if previous_status else "—"
        form = StaffLeadStatusForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save(commit=False)
            status = lead.staff_status
            lost_reason = form.cleaned_data.get("lost_reason_type")
            note = (form.cleaned_data.get("status_change_note") or "").strip()

            if is_staff_lost_status(status):
                lead.lost_reason_type = lost_reason
            else:
                lead.lost_reason_type = None

            stage = staff_status_to_stage(status)
            if stage:
                lead.staff_stage = stage

            new_followup_handoff = status.sends_to_followup and not lead.sent_to_followup_at
            if new_followup_handoff:
                lead.sent_to_followup_at = timezone.now()
                lead.pipeline_stage = Lead.PipelineStage.FOLLOWUP
                if not lead.followup_status_id:
                    lead.followup_status = get_followup_queue_default_status()

            update_fields = ["staff_status", "lost_reason_type", "staff_stage", "updated_at"]
            if new_followup_handoff:
                update_fields.extend(["sent_to_followup_at", "pipeline_stage", "followup_status"])
            lead.save(update_fields=update_fields)

            history_note = note
            if is_staff_lost_status(status) and lost_reason:
                reason_line = f"Lost reason: {lost_reason.name}"
                history_note = f"{reason_line}\n{note}".strip() if note else reason_line

            LeadStaffStatusHistory.objects.create(
                lead=lead,
                from_status_name=previous_status_name,
                to_status=status,
                lost_reason_type=lost_reason if is_staff_lost_status(status) else None,
                note=history_note,
                created_by=request.user,
            )

            roadmap_note = history_note or (
                f"Staff sent lead to follow-up team ({status.name})."
                if status.sends_to_followup
                else f"Staff updated status to {status.name}."
            )
            lead.roadmap_entries.create(
                created_by=request.user,
                title=f"Staff status: {status.name}",
                note=roadmap_note,
            )
            if status.sends_to_followup:
                messages.success(request, f"Lead {lead.display_id} sent to follow-up team.")
            elif is_staff_lost_status(status):
                messages.success(request, f"Lead {lead.display_id} marked as Lost ({lost_reason.name}).")
            else:
                messages.success(request, f"Lead {lead.display_id} status set to {status.name}.")
            return redirect(STAFF_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.STAFF,
            "portal/leads/staff_list.html",
            "My Leads",
            active_nav="leads",
            **_staff_lead_context(
                request,
                status_lead=lead,
                lead_status_form=form,
                show_lead_status_modal=True,
            ),
        )

    return view


def _backoffice_pending_context(request, **extra):
    filters = parse_lead_list_filters(request)
    pending_qs = apply_lead_list_filters(
        backoffice_pending_leads_for_user(request.user)
        .select_related("created_by", "branch", "source", "service", "staff_status", "followup_status")
        .prefetch_related(
            documents_prefetch(),
            Prefetch("procedure_steps", queryset=LeadProcedureStep.objects.select_related("procedure", "reviewed_by")),
            Prefetch(
                "extracted_documents",
                queryset=LeadExtractedDocument.objects.order_by("original_name"),
            ),
        )
        .order_by("-sent_to_backoffice_at", "-created_at"),
        filters,
    )
    defaults = {
        "pending_leads": pending_qs,
        "pending_leads_count": pending_qs.count(),
        "filters_active": filters_are_active(filters),
        **lead_filter_context(filters, show_staff=True, show_followup=True),
        "check_form": BackofficeCheckForm(),
    }
    defaults.update(extra)
    return defaults


def _backoffice_leads_base_queryset(user):
    return (
        backoffice_accessible_leads_queryset(user)
        .select_related(
            "created_by", "branch", "staff_status", "followup_status", "service", "backoffice_checked_by"
        )
        .prefetch_related(
            documents_prefetch(),
            Prefetch("procedure_steps", queryset=LeadProcedureStep.objects.select_related("procedure", "reviewed_by")),
            Prefetch(
                "extracted_documents",
                queryset=LeadExtractedDocument.objects.order_by("original_name"),
            ),
        )
    )


def _paginate_backoffice_leads(request, queryset):
    paginator = Paginator(queryset, BACKOFFICE_LEADS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def backoffice_pending_list_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @backoffice_head_required()
    def view(request):
        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/leads/backoffice_pending.html",
            "Pending verification",
            active_nav="pending",
            is_backoffice_head=True,
            **_backoffice_pending_context(request),
        )

    return view


def backoffice_all_leads_list_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    def view(request):
        filters = parse_lead_list_filters(request)
        base_qs = _backoffice_leads_base_queryset(request.user)
        if not user_is_backoffice_head(request.user):
            base_qs = filter_backoffice_procedure_completed(base_qs)
        queryset = apply_lead_list_filters(
            base_qs.order_by("-sent_to_backoffice_at", "-created_at"),
            filters,
        )
        page_obj = _paginate_backoffice_leads(request, queryset)
        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/leads/backoffice_all_leads.html",
            "Leads",
            active_nav="all_leads",
            page_obj=page_obj,
            leads=page_obj.object_list,
            total_count=page_obj.paginator.count,
            filters_active=filters_are_active(filters),
            is_backoffice_head=user_is_backoffice_head(request.user),
            **lead_filter_context(filters, show_staff=True, show_followup=True, show_backoffice=True),
        )

    return view


def backoffice_team_pending_leads_list_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @backoffice_team_only_required()
    def view(request):
        filters = parse_lead_list_filters(request)
        base_qs = filter_backoffice_procedure_in_progress(
            _backoffice_leads_base_queryset(request.user).filter(
                backoffice_status=Lead.BackofficeStatus.VERIFIED,
            )
        )
        queryset = apply_lead_list_filters(
            base_qs.order_by("-sent_to_backoffice_at", "-created_at"),
            filters,
        )
        page_obj = _paginate_backoffice_leads(request, queryset)
        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/leads/backoffice_team_pending_leads.html",
            "Pending leads",
            active_nav="pending_leads",
            page_obj=page_obj,
            leads=page_obj.object_list,
            total_count=page_obj.paginator.count,
            filters_active=filters_are_active(filters),
            is_backoffice_head=False,
            **lead_filter_context(filters, show_staff=True, show_followup=True, show_backoffice=True),
        )

    return view


def backoffice_lead_list_view():
    """Legacy alias — redirects to pending verification."""
    return backoffice_pending_list_view()


def backoffice_lead_verify_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @backoffice_head_required()
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(
            Lead,
            pk=pk,
            backoffice_status=Lead.BackofficeStatus.PENDING,
            sent_to_backoffice_at__isnull=False,
        )
        form = BackofficeCheckForm(request.POST)
        notes = form.cleaned_data["notes"] if form.is_valid() else ""
        lead.mark_backoffice_verified(request.user, notes)
        lead.followup_assigned_to = None
        lead.save(update_fields=["followup_assigned_to", "updated_at"])
        messages.success(request, f"{lead.display_id} marked as correct — ready for case processing.")
        return redirect(BACKOFFICE_PENDING_LIST)

    return view


def backoffice_lead_reject_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @backoffice_head_required()
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(
            Lead,
            pk=pk,
            backoffice_status=Lead.BackofficeStatus.PENDING,
            sent_to_backoffice_at__isnull=False,
        )
        form = BackofficeCheckForm(request.POST)
        notes = form.cleaned_data["notes"] if form.is_valid() else ""
        lead.mark_backoffice_rejected(request.user, notes)
        messages.warning(request, f"{lead.display_id} marked as not correct. Staff can see this status.")
        return redirect(BACKOFFICE_PENDING_LIST)

    return view


def _backoffice_leads_with_pending_procedures_queryset():
    """Verified leads that have procedure steps waiting for team review."""
    lead_ids = (
        LeadProcedureStep.objects.filter(
            status=LeadProcedureStep.Status.PENDING,
            lead__backoffice_status=Lead.BackofficeStatus.VERIFIED,
            lead__sent_to_backoffice_at__isnull=False,
        )
        .values_list("lead_id", flat=True)
        .distinct()
    )
    return (
        Lead.objects.filter(pk__in=lead_ids)
        .select_related("created_by", "branch", "source", "service", "staff_status", "followup_status")
        .prefetch_related(
            documents_prefetch(),
            Prefetch(
                "procedure_steps",
                queryset=LeadProcedureStep.objects.select_related("procedure", "reviewed_by"),
            ),
            Prefetch(
                "extracted_documents",
                queryset=LeadExtractedDocument.objects.order_by("original_name"),
            ),
        )
    )


def _backoffice_procedure_context(request, **extra):
    filters = parse_lead_list_filters(request)
    procedure_qs = apply_lead_list_filters(
        _backoffice_leads_with_pending_procedures_queryset().order_by("-updated_at"),
        filters,
    )
    defaults = {
        "procedure_leads": procedure_qs,
        "procedure_leads_count": procedure_qs.count(),
        "filters_active": filters_are_active(filters),
        **lead_filter_context(filters, show_staff=True, show_followup=True),
    }
    defaults.update(extra)
    return defaults


def backoffice_procedure_pending_list_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @backoffice_team_only_required()
    def view(request):
        return render_portal_page(
            request,
            UserProfile.UserType.BACKOFFICE,
            "portal/leads/backoffice_procedure_pending.html",
            "Procedure review",
            active_nav="procedures",
            is_backoffice_head=False,
            **_backoffice_procedure_context(request),
        )

    return view


def backoffice_procedure_review_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @backoffice_team_only_required()
    @require_http_methods(["POST"])
    def view(request, step_id):
        step = get_object_or_404(
            LeadProcedureStep.objects.select_related("lead", "procedure"),
            pk=step_id,
            status=LeadProcedureStep.Status.PENDING,
            lead__backoffice_status=Lead.BackofficeStatus.VERIFIED,
        )
        form = BackofficeProcedureReviewForm(request.POST, request.FILES)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(BACKOFFICE_PROCEDURE_LIST)

        typist_checked = form.cleaned_data["typist_checked"]
        document = form.cleaned_data.get("backoffice_document")
        note = (form.cleaned_data.get("review_note") or "").strip()
        
        if typist_checked:
            step.status = LeadProcedureStep.Status.APPROVED
            if document:
                step.backoffice_document = document
            outcome_label = "approved"
        else:
            step.status = LeadProcedureStep.Status.REJECTED
            outcome_label = "rejected"
            
        step.review_note = note
        step.reviewed_by = request.user
        step.reviewed_at = timezone.now()
        step.save(update_fields=["status", "backoffice_document", "review_note", "reviewed_by", "reviewed_at", "updated_at"])

        step.lead.roadmap_entries.create(
            created_by=request.user,
            title=f"Procedure {outcome_label}: {step.procedure.name}",
            note=note or f"Back office team {outcome_label} the submitted procedure step.",
        )
        messages.success(request, f"{step.lead.display_id}: {step.procedure.name} {outcome_label}.")
        return redirect(BACKOFFICE_PROCEDURE_LIST)

    return view


def _followup_lead_context(request, **extra):
    filters = parse_lead_list_filters(request)
    base_qs = filter_leads_procedure_in_progress(_followup_lead_queryset())
    leads = apply_lead_list_filters(base_qs, filters)
    defaults = {
        "leads": leads,
        "total_count": leads.count(),
        "filters_active": filters_are_active(filters),
        **lead_filter_context(filters, show_staff=True, show_followup=True),
        "lead_statuses": get_followup_lead_statuses(),
        "document_types": LeadDocument.DocType.choices,
        "followup_check_form": None,
        "followup_status_form": FollowupLeadStatusForm(),
        "followup_expire_form": FollowupServiceExpireForm(),
        "followup_procedure_form": None,
        "show_followup_check_modal": False,
        "show_followup_status_modal": False,
        "show_followup_expire_modal": False,
        "show_followup_procedure_modal": False,
        "check_lead": None,
        "status_lead": None,
        "expire_lead": None,
        "procedure_lead": None,
        "pending_backoffice_count": backoffice_pending_leads_queryset().count(),
    }
    defaults.update(extra)
    return defaults


def followup_lead_list_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    def view(request):
        return render_portal_page(
            request,
            UserProfile.UserType.FOLLOWUP,
            "portal/leads/followup_list.html",
            "Follow-up Leads",
            active_nav="leads",
            **_followup_lead_context(request),
        )

    return view


def _followup_leads_base_queryset():
    return (
        followup_sent_leads_queryset()
        .annotate(
            doc_count=Count("documents", distinct=True),
            extracted_doc_count=Count("extracted_documents", distinct=True),
        )
        .select_related(
            "created_by", "branch", "followup_assigned_to", "staff_status", "followup_status", "service", "source"
        )
        .prefetch_related(
            documents_prefetch(),
            Prefetch("procedure_steps", queryset=LeadProcedureStep.objects.select_related("procedure", "reviewed_by")),
            Prefetch(
                "extracted_documents",
                queryset=LeadExtractedDocument.objects.order_by("original_name"),
            ),
        )
    )


def _paginate_followup_leads(request, queryset):
    paginator = Paginator(queryset, FOLLOWUP_LEADS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def followup_all_leads_list_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    def view(request):
        filters = parse_lead_list_filters(request)
        queryset = apply_lead_list_filters(
            filter_leads_procedure_completed(_followup_lead_queryset()),
            filters,
        )
        page_obj = _paginate_followup_leads(request, queryset)
        return render_portal_page(
            request,
            UserProfile.UserType.FOLLOWUP,
            "portal/leads/followup_all_leads.html",
            "Leads",
            active_nav="all_leads",
            page_obj=page_obj,
            leads=page_obj.object_list,
            total_count=page_obj.paginator.count,
            filters_active=filters_are_active(filters),
            **lead_filter_context(filters, show_staff=True, show_followup=True),
        )

    return view


def _followup_lead_queryset():
    return (
        followup_team_leads_queryset()
        .annotate(
            doc_count=Count("documents", distinct=True),
            extracted_doc_count=Count("extracted_documents", distinct=True),
        )
        .select_related(
            "created_by", "branch", "followup_assigned_to", "staff_status", "followup_status", "service", "source"
        )
        .prefetch_related(
            documents_prefetch(),
            Prefetch("procedure_steps", queryset=LeadProcedureStep.objects.select_related("procedure", "reviewed_by")),
            Prefetch(
                "extracted_documents",
                queryset=LeadExtractedDocument.objects.order_by("original_name"),
            ),
        )
        .order_by("-sent_to_followup_at", "-created_at")
    )


def followup_lead_check_docs_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(followup_team_leads_queryset(), pk=pk)
        form = FollowupZipCheckForm(lead, request.POST)
        if form.is_valid():
            form.save_checks()
            lead.followup_assigned_to = request.user
            lead.save(update_fields=["followup_assigned_to", "updated_at"])
            lead.roadmap_entries.create(
                created_by=request.user,
                title="Staff ZIP checked",
                note="Follow-up verified all files from the staff ZIP.",
            )
            messages.success(request, f"Staff ZIP files checked for {lead.display_id}.")
            return redirect(FOLLOWUP_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.FOLLOWUP,
            "portal/leads/followup_list.html",
            "Follow-up Leads",
            active_nav="leads",
            **_followup_lead_context(
                request,
                check_lead=lead,
                followup_check_form=form,
                show_followup_check_modal=True,
            ),
        )

    return view


def followup_lead_status_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(followup_team_leads_queryset(), pk=pk)
        form = FollowupLeadStatusForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.followup_assigned_to = request.user
            note = form.cleaned_data.get("roadmap_note", "")
            status = lead.followup_status

            if followup_status_sends_to_backoffice(status):
                lead.sent_to_backoffice_at = timezone.now()
                lead.backoffice_status = Lead.BackofficeStatus.PENDING
                lead.backoffice_checked_by = None
                lead.backoffice_checked_at = None
                lead.backoffice_notes = ""
                lead.save()
                lead.roadmap_entries.create(
                    created_by=request.user,
                    title=f"Approved → Back office ({status.name})",
                    note=note or f"Follow-up approved lead — sent to back office as {status.name}.",
                )
                messages.success(request, f"{lead.display_id} approved and sent to back office.")
                return redirect(FOLLOWUP_LEAD_LIST)

            if followup_status_is_converted(status):
                if not lead.branch_id:
                    messages.error(
                        request,
                        f"{lead.display_id} has no branch (staff must add leads from a branch).",
                    )
                    return redirect(FOLLOWUP_LEAD_LIST)
                ok, case, handoff_msg = apply_converted_lead_handoff(lead, request.user, note=note)
                if ok:
                    lead.save()
                    messages.success(request, f"{lead.display_id} — {handoff_msg}")
                else:
                    messages.error(request, handoff_msg)
                return redirect(FOLLOWUP_LEAD_LIST)

            lead.pipeline_stage = Lead.PipelineStage.FOLLOWUP
            lead.save()
            title = f"Follow-up: {status.name}"
            lead.roadmap_entries.create(created_by=request.user, title=title, note=note)
            messages.success(request, f"{lead.display_id} status updated.")
            return redirect(FOLLOWUP_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.FOLLOWUP,
            "portal/leads/followup_list.html",
            "Follow-up Leads",
            active_nav="leads",
            **_followup_lead_context(
                request,
                status_lead=lead,
                followup_status_form=form,
                show_followup_status_modal=True,
            ),
        )

    return view


def followup_lead_expire_date_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(followup_team_leads_queryset(), pk=pk)
        form = FollowupServiceExpireForm(request.POST, instance=lead)
        if form.is_valid():
            old_date = lead.service_expire_date
            lead = form.save(commit=False)
            lead.followup_assigned_to = request.user
            lead.save(update_fields=["service_expire_date", "followup_assigned_to", "updated_at"])
            if lead.service_expire_date != old_date:
                if lead.service_expire_date:
                    note = lead.service_expire_date.strftime("%d %b %Y")
                else:
                    note = "Date cleared"
                lead.roadmap_entries.create(
                    created_by=request.user,
                    title="Service expire date updated",
                    note=note,
                )
            messages.success(request, f"Service expiry saved for {lead.display_id}.")
            return redirect(request.META.get("HTTP_REFERER") or FOLLOWUP_LEAD_LIST)
        else:
            messages.error(request, "Invalid expiry date provided.")
            return redirect(request.META.get("HTTP_REFERER") or FOLLOWUP_LEAD_LIST)

    return view


def followup_lead_update_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(followup_team_leads_queryset(), pk=pk)
        form = FollowupLeadForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.followup_assigned_to = request.user
            note = form.cleaned_data.get("roadmap_note", "")
            status = lead.followup_status

            if followup_status_sends_to_backoffice(status):
                lead.sent_to_backoffice_at = timezone.now()
                lead.backoffice_status = Lead.BackofficeStatus.PENDING
                lead.backoffice_checked_by = None
                lead.backoffice_checked_at = None
                lead.backoffice_notes = ""
                lead.save()
                lead.roadmap_entries.create(
                    created_by=request.user,
                    title=f"Approved → Back office ({status.name})",
                    note=note or f"Follow-up approved lead — sent to back office as {status.name}.",
                )
                messages.success(request, f"{lead.display_id} approved and sent to back office.")
                return redirect(FOLLOWUP_LEAD_LIST)

            if followup_status_is_converted(status):
                if not lead.branch_id:
                    messages.error(
                        request,
                        f"{lead.display_id} has no branch (staff must add leads from a branch).",
                    )
                    return redirect(FOLLOWUP_LEAD_LIST)
                ok, case, handoff_msg = apply_converted_lead_handoff(lead, request.user, note=note)
                if ok:
                    lead.save()
                    messages.success(request, f"{lead.display_id} — {handoff_msg}")
                else:
                    messages.error(request, handoff_msg)
                return redirect(FOLLOWUP_LEAD_LIST)

            lead.pipeline_stage = Lead.PipelineStage.FOLLOWUP
            lead.save()
            title = f"Follow-up: {status.name}"
            lead.roadmap_entries.create(created_by=request.user, title=title, note=note)
            messages.success(request, f"{lead.display_id} updated.")
            return redirect(FOLLOWUP_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.FOLLOWUP,
            "portal/leads/followup_list.html",
            "Follow-up Leads",
            active_nav="leads",
            **_followup_lead_context(
                request,
                edit_lead=lead,
                followup_form=form,
                show_followup_modal=True,
            ),
        )

    return view


def followup_lead_procedure_submit_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(followup_team_leads_queryset(), pk=pk)
        form = FollowupProcedureStepForm(lead, request.POST, request.FILES)
        if form.is_valid():
            procedure = form.cleaned_data["procedure"]
            existing = form.cleaned_data.get("existing_step")
            document = form.cleaned_data["document"]
            followup_note = (form.cleaned_data.get("followup_note") or "").strip()
            if existing:
                existing.status = LeadProcedureStep.Status.PENDING
                existing.document = document
                existing.followup_note = followup_note
                existing.submitted_by = request.user
                existing.review_note = ""
                existing.reviewed_by = None
                existing.reviewed_at = None
                existing.save(
                    update_fields=[
                        "status",
                        "document",
                        "followup_note",
                        "submitted_by",
                        "review_note",
                        "reviewed_by",
                        "reviewed_at",
                        "updated_at",
                    ]
                )
                step = existing
            else:
                step = LeadProcedureStep.objects.create(
                    lead=lead,
                    procedure=procedure,
                    status=LeadProcedureStep.Status.PENDING,
                    document=document,
                    followup_note=followup_note,
                    submitted_by=request.user,
                )
            lead.followup_assigned_to = request.user
            lead.save(update_fields=["followup_assigned_to", "updated_at"])
            lead.roadmap_entries.create(
                created_by=request.user,
                title=f"Procedure submitted: {procedure.name}",
                note=followup_note or "Sent to back office for procedure approval.",
            )
            messages.success(request, f"{lead.display_id}: step '{procedure.name}' sent for back office approval.")
            return redirect(FOLLOWUP_LEAD_LIST)

        return render_portal_page(
            request,
            UserProfile.UserType.FOLLOWUP,
            "portal/leads/followup_list.html",
            "Follow-up Leads",
            active_nav="leads",
            **_followup_lead_context(
                request,
                procedure_lead=lead,
                followup_procedure_form=form,
                show_followup_procedure_modal=True,
            ),
        )

    return view


def branch_lead_history_view():
    @portal_role_required(UserProfile.UserType.BRANCH)
    def view(request):
        manager = getattr(request.user, "branch_manager_profile", None)
        branch = manager.branch if manager else None
        filters = parse_monitoring_params(request, default_period="all")
        queryset = branch_monitoring_queryset(branch, filters) if branch else Lead.objects.none()
        paginator = Paginator(queryset, BRANCH_LEADS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        query = request.GET.copy()
        query.pop("page", None)
        filter_ctx = lead_filter_context(
            filters,
            show_staff=True,
            show_followup=True,
            show_backoffice=True,
        )
        filter_ctx["pagination_query"] = query.urlencode()
        return render_portal_page(
            request,
            UserProfile.UserType.BRANCH,
            "portal/leads/branch_monitoring.html",
            "Lead tracking history",
            active_nav="lead_history",
            branch=branch,
            lead_cards=monitoring_lead_cards(page_obj.object_list),
            monitoring_filters=filters,
            total_count=queryset.count(),
            page_obj=page_obj,
            filters_active=filters_are_active(filters),
            **filter_ctx,
        )

    return view


def branch_all_leads_list_view():
    @portal_role_required(UserProfile.UserType.BRANCH)
    def view(request):
        manager = getattr(request.user, "branch_manager_profile", None)
        branch = manager.branch if manager else None
        filters = parse_lead_list_filters(request)
        queryset = (
            apply_lead_list_filters(branch_leads_queryset(branch), filters)
            if branch
            else Lead.objects.none()
        )
        paginator = Paginator(queryset, BRANCH_LEADS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return render_portal_page(
            request,
            UserProfile.UserType.BRANCH,
            "portal/leads/branch_all_leads.html",
            "All leads",
            active_nav="all_leads",
            branch=branch,
            leads=page_obj.object_list,
            page_obj=page_obj,
            total_count=queryset.count(),
            filters_active=filters_are_active(filters),
            **lead_filter_context(filters, show_staff=True, show_followup=True, show_backoffice=True),
        )

    return view
