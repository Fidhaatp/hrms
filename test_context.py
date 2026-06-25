from django.contrib.auth.models import User
from core.context_processors import portal_notifications
class DummyReq:
    def __init__(self):
        self.user = User.objects.get(username='shahul')
        self.is_authenticated = True
print(portal_notifications(DummyReq()))
