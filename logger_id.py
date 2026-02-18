import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from django.db.models import Q
from formapp.models import reestr, reestInfo, files, contracts
from changelog.models import ChangeLog
logs = ChangeLog.objects.all()
for l in logs:
    if l.object_id == 0:
        if l.model == "Реестры":
            try:
                dogovor = contracts.objects.filter(number='110/'+l.record_id[:4]+"-Д")
                r = reestInfo.objects.filter((Q(project_dogovor=dogovor[0]) & Q(num_reestr=l.record_id[5:])))
                l.object_id = r[0].id
                l.save()
                print(l.record_id, l.object_id)
            except Exception:
                print(l.record_id, "не обнаружен")
        elif l.model == "Замечания":
            try:
                ss1 = l.record_id.index("/")
                ss2 = l.record_id.index("/", ss1+1)
                dogovor = contracts.objects.filter(number='110/'+l.record_id[:4]+"-Д")
                print(dogovor)
                print(dogovor[0], l.record_id[5:ss1], l.record_id[ss1+1:ss2], int(l.record_id[ss2+1]))
                r = reestr.objects.filter((Q(project_dogovor=dogovor[0]) & Q(num_reestr=l.record_id[5:ss1]) &
                                                    Q(num_remark=l.record_id[ss1+1:ss2]) & Q(remark_v=int(l.record_id[ss2+1]))))
                l.object_id = r[0].id
                l.save()
                print(l.record_id, l.object_id)
            except Exception:
                print(l.record_id, "не обнаружено")
        elif l.model == "Файлы":
            try:
                f = files.objects.filter(file=l.record_id)
                l.object_id = f[0].id
                l.save()
                print(l.record_id, l.object_id)
            except Exception:
                print(l.record_id, "не обнаружен")