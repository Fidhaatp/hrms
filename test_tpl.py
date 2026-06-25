from django.template import Template, Context
from django.contrib.auth.models import User
t = Template("{% if request.user.profile.user_type == 'hr' %}YES{% else %}NO{% endif %}")
class Req:
    user = User.objects.get(username='shahul')
print(t.render(Context({'request': Req()})))
