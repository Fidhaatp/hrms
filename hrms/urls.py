from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.static import serve as static_serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("admin-portal/", include("admin_portal.urls")),
    path("hr/", include("hr.urls")),
    path("backoffice/", include("backoffice.urls")),
    path("staff/", include("staff.urls")),
    path("followup/", include("followup.urls")),
    path("branch/", include("branch.urls")),
    path("finance/", include("finance.urls")),
    path("marketing/", include("marketing.urls")),
    path("accountant/", include("accountant.urls")),
    path("sitemap.xml", TemplateView.as_view(template_name="sitemap.xml", content_type="text/xml")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]  # Static/media routes added below (work even if DEBUG=False)

admin.site.site_header = "PROJECT Administration"
admin.site.site_title = "PROJECT Admin Portal"
admin.site.index_title = "Welcome to PROJECT Admin Portal"

# Custom error pages
handler400 = 'core.views.custom_400'
handler403 = 'core.views.custom_403'
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'

# Serve static/media files.
# Django's built-in `static()` URL helper only works when DEBUG=True.
# Since you want custom error pages (DEBUG=False), we serve them manually here.
#
# Note: This is fine for local dev; in production Apache/Nginx should serve /static.
static_root = None
if getattr(settings, "STATICFILES_DIRS", None):
    # Serve from the original `static/` folder first (no need for collectstatic).
    static_root = settings.STATICFILES_DIRS[0]
if static_root is None:
    static_root = settings.STATIC_ROOT

urlpatterns += [
    path(f"{settings.STATIC_URL.lstrip('/') }<path:path>", static_serve, {"document_root": str(static_root)}),
    path(f"{settings.MEDIA_URL.lstrip('/') }<path:path>", static_serve, {"document_root": str(settings.MEDIA_ROOT)}),
]