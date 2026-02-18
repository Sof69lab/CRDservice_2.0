import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from formapp.models import reestr, reestInfo
reestrs = reestInfo.objects.all()
for r in reestrs:
    r.reestr_index = r.project_dogovor.number+'_'+r.num_reestr
    r.save()
remarks = reestr.objects.all()
for r in remarks:
    if r.responsibleTrouble_name is not None:
        r.remark_index = r.reestrID.reestr_index+'_'+r.num_remark+'_'+str(r.remark_v)+'_'+str(r.responsibleTrouble_name.id)
        r.save()