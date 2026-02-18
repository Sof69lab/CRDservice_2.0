import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager

file_path = "/home/user/Документы/webCRDS/Учзгенпас24.csv"
file = open(file_path, mode='rt')
data = list(file)
file.close()
del data[0]
del data[75:]
forWrite = []
for i in data:
    first_space = i.index(" ")
    first_semicolon = i.index(";")
    second_semicolon = i.index(";", first_semicolon+1)
    last_name = i[0:first_space]
    first_name = i[first_space+1:first_semicolon]
    username = i[first_semicolon+1:second_semicolon]
    email = username+"@vnipipt.ru"
    pw = BaseUserManager().make_random_password(13)
    if username != '':
        if User.objects.get(username=username):
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(username=username, first_name=first_name,
                                        last_name=last_name, email=email)
        user.set_password(pw)
        user.save()
        forWrite.append(username + " " + pw + "\n")
file_path = "/home/user/Документы/webCRDS/Учзгенпас24.txt"
file = open(file_path, mode='w')
file.writelines(forWrite)
file.close()
