from core.dashboard_metrics import marketing_dashboard
from core.models import Announcement, Lead, MarketingCampaign, UserProfile
from core.portal import portal_role_required, render_portal_page
from core.portal_pages import client_journey_steps, marketing_module_stats, quick_link, render_module


@portal_role_required(UserProfile.UserType.MARKETING)
def index(request):
    return render_portal_page(
        request,
        UserProfile.UserType.MARKETING,
        "marketing/dashboard.html",
        "Dashboard",
        metrics=marketing_dashboard(),
    )


@portal_role_required(UserProfile.UserType.MARKETING)
def campaigns(request):
    rows = [
        [c.name, c.get_channel_display(), c.leads_count, "Active" if c.is_active else "Inactive"]
        for c in MarketingCampaign.objects.all()[:30]
    ]
    return render_module(
        request,
        UserProfile.UserType.MARKETING,
        page_title="Campaigns",
        active_nav="campaigns",
        module_title="Marketing Campaigns",
        module_intro="Facebook, Google Ads, WhatsApp, and other campaigns.",
        stats=marketing_module_stats(),
        extra_table_headers=["Campaign", "Channel", "Leads", "Status"],
        extra_rows=rows,
    )


@portal_role_required(UserProfile.UserType.MARKETING)
def creatives(request):
    return render_module(
        request,
        UserProfile.UserType.MARKETING,
        page_title="Creatives",
        active_nav="creatives",
        module_title="Creatives",
        module_intro="Posters, videos, brochures, and marketing assets.",
    )


@portal_role_required(UserProfile.UserType.MARKETING)
def leads(request):
    count = Lead.objects.count()
    return render_module(
        request,
        UserProfile.UserType.MARKETING,
        page_title="Lead Generation",
        active_nav="leads",
        module_title="Lead Generation",
        module_intro="Campaign leads and source tracking.",
        workflow_steps=client_journey_steps(),
        stats=[{"label": "Total CRM leads", "value": count}],
        quick_links=[
            quick_link("Lead sources (HR)", "hr:lead_sources", "bi-signpost-split"),
            quick_link("All leads (HR)", "hr:leads", "bi-funnel"),
        ],
    )


@portal_role_required(UserProfile.UserType.MARKETING)
def announcements(request):
    rows = [
        [a.title, a.created_at.strftime("%d %b %Y"), "Active" if a.is_active else "Inactive"]
        for a in Announcement.objects.all()[:20]
    ]
    return render_module(
        request,
        UserProfile.UserType.MARKETING,
        page_title="Announcements",
        active_nav="announcements",
        module_title="Marketing Announcements",
        module_intro="Company notices and marketing updates.",
        extra_table_headers=["Title", "Date", "Status"],
        extra_rows=rows,
    )
