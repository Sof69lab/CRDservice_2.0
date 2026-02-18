import os
import django
import pandas as pd
import numpy as np
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager

# чтение файла с информацией о субподрядчиках
db = pd.read_excel("/home/user/Документы/webCRDS/Субподряд от 26.07.2024.xlsx", header=2)
subcontracts = np.unique(np.array(db.iloc[:, 3]))
# запись в БД
index = len(User.objects.filter(groups=4))
for i in subcontracts:
    last_name = i
    first_name = " "
    username = "subcontracts" + str(index)
    pw = BaseUserManager().make_random_password(13)
    if len(User.objects.filter(last_name=last_name)) == 0:
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
        user.set_password(pw)
        user.groups.add(4)
        user.save()
    index += 1
