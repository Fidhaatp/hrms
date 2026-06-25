import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")
django.setup()

from core.models import Lead
from django.db.models import Q
leads = Lead.objects.filter(Q(name__icontains='lead') | Q(phone__icontains='lead'))
print(f"Found {leads.count()} leads")
for l in leads:
    print(l.name, l.phone)
