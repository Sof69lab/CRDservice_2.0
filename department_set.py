import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from formapp.models import reestr, departments

remarks = reestr.objects.all()
for r in remarks:
    respons = r.responsibleTrouble_name
    if respons is not None:
        print(respons)
        department = departments.objects.get(user=respons)
        if department:
            r.department = department.department
            r.save()
            print(r.project_dogovor, r.num_reestr, r.num_remark, r.department)