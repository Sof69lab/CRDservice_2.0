import sys, os, json
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from formapp.models import reestr, reestInfo
from changelog.models import ChangeLog
from django.db.models import Q

remarks = reestr.objects.all()
for r in remarks:
    print(r.remark_index, r.create_date)
    # create_date = ChangeLog.objects.filter((Q(model="Замечания") & Q(object_id=r.id) & Q(action_on_model="создал(а)")))
    # if len(create_date) > 0:
    #     r.create_date = create_date[0].changed
    # else:
    #     r.create_date = reestInfo.objects.get(id=r.reestrID.id).start_date
    # r.save()