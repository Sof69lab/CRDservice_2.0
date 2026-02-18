import os
import django
import pandas as pd
import datetime
import numpy as np
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formsite.settings')
django.setup()
from formapp.models import customers, contracts, reviewers
# чтение файла с информацией о договорах
# db = pd.read_excel("/home/user/Документы/webCRDS/2024__08_Август_Отчет по заключенным договорам (доходные).xlsx", sheet_name=None, header=7)
# db = list(db.values())
# cstmrs = []
# dogovors = []
# format_str = '%d.%m.%Y'
# for i in db:
#     i = i.loc[:, ['Наименование краткое', 'Серия и номер документа, удостоверяющего личность руководителя', '№ и дата', 'Предмет договора']]
#     i = i.dropna(how='all')
#     for j in range(len(i)):
#         customer = i.iloc[j]['Наименование краткое']
#         num = i.iloc[j]['Серия и номер документа, удостоверяющего личность руководителя']
#         try:
#             numStart = num.index('110/')
#             num = num[numStart:num.index('Д', numStart)+1]
#         except Exception:
#             print(num)
#         datetime_obj = i.iloc[j]['№ и дата']
#         if isinstance(datetime_obj, str):
#             datetime_obj = datetime.datetime.strptime(datetime_obj, format_str)
#         name = i.iloc[j]['Предмет договора']
#         cstmrs.append(customer)
#         dogovors.append([customer, num, datetime_obj, name])
# cstmrs = np.unique(np.array(cstmrs))

# добавление заказчиков и рецензентов
# saved_customers = customers.objects.all()
# for i in saved_customers:
#     i = i.name
# for i in cstmrs:
#     if i not in saved_customers:
#         customers.objects.create(name=i)
#         reviewers.objects.create(name=i)

# добавление рецензентов
rvwrs = ['АО «ВНИПИпромтехнологии»', 'ФАУ «Главгосэкспертиза России»', 'Ведомственная экспертиза ГК «Росатом»', 'ЦКР-ТПИ Роснедр']
for i in rvwrs:
    reviewers.objects.create(name=i)
# добавление договоров
# for i in dogovors:
#     try:
#         customer = customers.objects.filter(name=i[0])[0]
#         contracts.objects.create(customer=customer, number=i[1], name=i[3], date=i[2])
#     except Exception:
#         print(i)
