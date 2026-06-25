import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import UserProfile

hr_user = UserProfile.objects.filter(user_type=UserProfile.UserType.HR).first().user

client = Client()
client.force_login(hr_user)
response = client.get('/notifications/')
print("Status Code:", response.status_code)
if response.status_code != 200:
    print(response.content.decode('utf-8'))
else:
    import re
    html = response.content.decode('utf-8')
    match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>[\s\S]*?Notifications[\s\S]*?</a>', html)
    if match:
        print("Found Notifications link:", match.group(0))
    else:
        print("Notifications link not found")

