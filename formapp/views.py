import sys, os
import datetime
from formapp.functions import *
from django.shortcuts import render
from django.utils import timezone
from formapp.forms import *
from formapp.models import reestr, reestInfo, files, contracts, customers, aiChatSession, aiChatMessage
from changelog.models import ChangeLog
from formapp.auto_remark import auto_import, auto_export
from formsite.settings import MEDIA_ROOT
from django.shortcuts import redirect
from django.db.models import Q, When, Value, Case, Exists, OuterRef
from django.db.models.functions import Length
from django.contrib import messages
from django.http import FileResponse, JsonResponse
import json
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

emptyUserID = User.objects.filter(last_name="1. Сотрудник больше не работает")[0].id

order_subquery = reestr.objects.filter(reestrID=OuterRef("pk")).exclude(status__in=["На согласовании Рецензентом", "Замечание снято"])

reestr_priority_order = Case(
    When(status="Формирование", then=Value(1)),
    When(status="На заполнении", then=Value(2)),
    When(status="На согласовании", then=Value(3)),
    When(status="На доработке", then=Value(4)),
    When(status="Согласовано ГИПом", then=Value(5)),
    When(status="Подготовка ответов", then=Value(6)),
    When((Q(status="На согласовании Рецензентом") & Exists(order_subquery)), then=Value(7)),
    When(status="На согласовании Рецензентом", then=Value(8)),
    When(status="Закрыт", then=Value(9)),
    When(status="Скрыт", then=Value(10)),
    default=Value(-1)
)
remark_priority_order = Case(
    When(status="Формирование", then=Value(1)),
    When(status="На заполнении ГИПом", then=Value(2)),
    When(status="На доработке ГИПом", then=Value(3)),
    When(status="На согласовании ГИПом", then=Value(4)),
    When(status="Подготовка ответов ГИПом", then=Value(5)),
    When(status="На заполнении руководителем", then=Value(6)),
    When(status="На доработке руководителем", then=Value(7)),
    When(status="На согласовании руководителем", then=Value(8)),
    When(status="Подготовка ответов руководителем", then=Value(9)),
    When(status="На заполнении исполнителем", then=Value(10)),
    When(status="На доработке исполнителем", then=Value(11)),
    When(status="Подготовка ответов исполнителем", then=Value(12)),
    When(status="На согласовании Рецензентом", then=Value(13)),
    When(status="Согласовано ГИПом", then=Value(14)),
    When(status="Принято ГИПом", then=Value(15)),
    When(status="Замечание снято", then=Value(16)),
    default=Value(-1)
)
remark_boss_priority_order = Case(
    When(status="На заполнении руководителем", then=Value(1)),
    When(status="На доработке руководителем", then=Value(2)),
    When(status="На согласовании руководителем", then=Value(3)),
    When(status="Подготовка ответов руководителем", then=Value(4)),
    When(status="На заполнении исполнителем", then=Value(5)),
    When(status="На доработке исполнителем", then=Value(6)),
    When(status="Подготовка ответов исполнителем", then=Value(7)),
    When(status="На заполнении ГИПом", then=Value(8)),
    When(status="На доработке ГИПом", then=Value(9)),
    When(status="На согласовании ГИПом", then=Value(10)),
    When(status="Подготовка ответов ГИПом", then=Value(11)),
    When(status="На согласовании Рецензентом", then=Value(12)),
    When(status="Согласовано ГИПом", then=Value(13)),
    When(status="Принято ГИПом", then=Value(14)),
    When(status="Замечание снято", then=Value(15)),
    default=Value(-1)
)
remark_employee_priority_order = Case(
    When(status="На заполнении исполнителем", then=Value(1)),
    When(status="На доработке исполнителем", then=Value(2)),
    When(status="Подготовка ответов исполнителем", then=Value(3)),
    When(status="На заполнении руководителем", then=Value(4)),
    When(status="На доработке руководителем", then=Value(5)),
    When(status="На согласовании руководителем", then=Value(6)),
    When(status="Подготовка ответов руководителем", then=Value(7)),
    When(status="На заполнении ГИПом", then=Value(8)),
    When(status="На доработке ГИПом", then=Value(9)),
    When(status="На согласовании ГИПом", then=Value(10)),
    When(status="Подготовка ответов ГИПом", then=Value(11)),
    When(status="На согласовании Рецензентом", then=Value(12)),
    When(status="Согласовано ГИПом", then=Value(13)),
    When(status="Принято ГИПом", then=Value(14)),
    When(status="Замечание снято", then=Value(15)),
    default=Value(-1)
)

MAX_FILE_UPLOAD = 30 * 1024 * 1024

def home(request):
    info = []
    excluded_status = ["Доработан", "Закрыт", "Формирование", "Скрыт"]
    try:
        department = departments.objects.get(user=request.user.id).department
        subs = departments.objects.get(user=request.user.id).substitute.all()
    except Exception:
        department = ""
        subs = []
    if request.user.groups.filter(name='ГИП').exists():
        group = 'ГИП'
        q1 = Q(gip=request.user) | Q(gip__in=subs)
        remarkList = reestr.objects.filter(
            ((Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True)))
        IDlist = []
        for r in remarkList:
            IDlist.append(r.reestrID.id)
        q2 = Q(id__in=IDlist)
        reestrs = reestInfo.objects.filter(q1 | q2).exclude(status="Скрыт").annotate(
            reestr_priority_order=reestr_priority_order).order_by('reestr_priority_order', 'project_dogovor',
                                                                  'num_reestr')
        #reviewer_sended = len(reestInfo.objects.filter(((q1 | q2) & Q(status="На согласовании Рецензентом"))))
        reviewer_sended_reestNum = []
        closed = len(reestInfo.objects.filter(((q1 | q2) & Q(status="Закрыт"))))
        #статистика
        for r in reestrs:
            remarks_all = []
            for i in reestr.objects.filter((Q(reestrID=r.id) & Q(actuality=True))):
                remarks_all.append([i.id, i.num_remark, i.status, i.total_importance])
            remarks_all = np.array(remarks_all)
            if r.status == "На согласовании Рецензентом":
                reviewed = True
                for re in remarks_all:
                    if re[2] not in ["На согласовании Рецензентом", "Замечание снято"]:
                        reviewed = False
                        break
                if reviewed:
                    reviewer_sended_reestNum.append(r)
            try:
                remarks, counts = np.unique(np.array(remarks_all[:, 1]), return_counts=True)  # всего, без дублирований
            except Exception:
                remarks = []
                counts = []
            uniq_row = []
            for i in range(len(counts)):
                if counts[i] > 1:
                    row_indices = np.where(remarks_all[:, 1] == remarks[i])[0]
                    importances = remarks_all[row_indices,3]
                    comm_imp = ""
                    if 'Существенное' in importances:
                        comm_imp = "Существенное"
                    elif 'В компетенции Заказчика' in importances:
                        comm_imp = "В компетенции Заказчика"
                    elif 'Несущественное' in importances:
                        comm_imp = "Несущественное"
                    statuses = remarks_all[row_indices, 2]
                    comm_stat = "В работе"
                    if all(x == "Замечание снято" for x in statuses):
                        comm_stat = "Замечание снято"
                    elif all(x in ["Замечание снято", "На соглсовании Рецензентом", "Принято ГИПом"] for x in statuses):
                        comm_stat = "Ответ подготовлен"
                    remarks_all[row_indices, 3] = comm_imp
                    remarks_all[row_indices, 2] = comm_stat
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
                else:
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
            remarks = len(remarks) # всего
            close = 0
            final = 0
            work = 0
            closeC = 0
            finalC = 0
            workC = 0
            closeS = 0
            finalS = 0
            workS = 0
            closeI = 0
            finalI = 0
            workI = 0
            customer = 0
            signific = 0
            insignific = 0
            for i in range(len(uniq_row)):
                if remarks_all[uniq_row[i], 3] == 'В компетенции Заказчика':
                    customer += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом", "На согласовании Рецензентом"]:
                        close += 1 # ответ подготовлен
                        closeC += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1 # закрыты
                        finalC += 1
                    else:
                        work += 1 # в работе
                        workC += 1
                elif remarks_all[uniq_row[i], 3] == 'Существенное':
                    signific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом", "На согласовании Рецензентом"]:
                        close += 1 # ответ подготовлен
                        closeS += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1 # закрыты
                        finalS += 1
                    else:
                        work += 1 # в работе
                        workS += 1
                elif remarks_all[uniq_row[i], 3] == 'Несущественное':
                    insignific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом", "На согласовании Рецензентом"]:
                        close += 1 # ответ подготовлен
                        closeI += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1 # закрыты
                        finalI += 1
                    else:
                        work += 1 # в работе
                        workI += 1
                else:
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом", "На согласовании Рецензентом"]:
                        close += 1 # ответ подготовлен
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1 # закрыты
                    else:
                        work += 1 # в работе

            info.append([r.id, remarks, customer, signific, insignific, work, close, final,
                         round(final * 100.0 / remarks, 2) if remarks else 0,
                         workC, closeC, finalC,
                         round(finalC * 100.0 / customer, 2) if customer else 0,
                         workS, closeS, finalS,
                         round(finalS * 100.0 / signific, 2) if signific else 0,
                         workI, closeI, finalI,
                         round(finalI * 100.0 / insignific, 2) if insignific else 0])
        reviewer_sended = len(reviewer_sended_reestNum)
    elif request.user.is_superuser:
        group = 'Администратор'
        reestrs = reestInfo.objects.all().annotate(reestr_priority_order=reestr_priority_order).order_by(
            'reestr_priority_order', 'project_dogovor', 'num_reestr')
        #reviewer_sended = len(reestInfo.objects.filter(Q(status="На согласовании Рецензентом")))
        reviewer_sended_reestNum = []
        closed = len(reestInfo.objects.filter(status__in=["Закрыт", "Скрыт"]))
        for r in reestrs:
            remarks_all = []
            for i in reestr.objects.filter(reestrID=r.id):
                remarks_all.append([i.id, i.num_remark, i.status, i.total_importance])
            remarks_all = np.array(remarks_all)
            if r.status == "На согласовании Рецензентом":
                reviewed = True
                for re in remarks_all:
                    if re[2] not in ["На согласовании Рецензентом", "Замечание снято"]:
                        reviewed = False
                        break
                if reviewed:
                    reviewer_sended_reestNum.append(r)
            try:
                remarks, counts = np.unique(np.array(remarks_all[:, 1]), return_counts=True)  # всего, без дублирований
            except Exception:
                remarks = []
                counts = []
            uniq_row = []
            for i in range(len(counts)):
                if counts[i] > 1:
                    row_indices = np.where(remarks_all[:, 1] == remarks[i])[0]
                    importances = remarks_all[row_indices, 3]
                    comm_imp = ""
                    if 'Существенное' in importances:
                        comm_imp = "Существенное"
                    elif 'В компетенции Заказчика' in importances:
                        comm_imp = "В компетенции Заказчика"
                    elif 'Несущественное' in importances:
                        comm_imp = "Несущественное"
                    statuses = remarks_all[row_indices, 2]
                    comm_stat = "В работе"
                    if all(x == "Замечание снято" for x in statuses):
                        comm_stat = "Замечание снято"
                    elif all(x in ["Замечание снято", "На соглсовании Рецензентом", "Принято ГИПом"] for x in statuses):
                        comm_stat = "Ответ подготовлен"
                    remarks_all[row_indices, 3] = comm_imp
                    remarks_all[row_indices, 2] = comm_stat
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
                else:
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
            remarks = len(remarks)  # всего
            close = 0
            final = 0
            work = 0
            closeC = 0
            finalC = 0
            workC = 0
            closeS = 0
            finalS = 0
            workS = 0
            closeI = 0
            finalI = 0
            workI = 0
            customer = 0
            signific = 0
            insignific = 0
            for i in range(len(uniq_row)):
                if remarks_all[uniq_row[i], 3] == 'В компетенции Заказчика':
                    customer += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeC += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalC += 1
                    else:
                        work += 1  # в работе
                        workC += 1
                elif remarks_all[uniq_row[i], 3] == 'Существенное':
                    signific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeS += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalS += 1
                    else:
                        work += 1  # в работе
                        workS += 1
                elif remarks_all[uniq_row[i], 3] == 'Несущественное':
                    insignific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeI += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalI += 1
                    else:
                        work += 1  # в работе
                        workI += 1
                else:
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                    else:
                        work += 1  # в работе

            info.append([r.id, remarks, customer, signific, insignific, work, close, final,
                         round(final * 100.0 / remarks, 2) if remarks else 0,
                         workC, closeC, finalC,
                         round(finalC * 100.0 / customer, 2) if customer else 0,
                         workS, closeS, finalS,
                         round(finalS * 100.0 / signific, 2) if signific else 0,
                         workI, closeI, finalI,
                         round(finalI * 100.0 / insignific, 2) if insignific else 0])
        reviewer_sended = len(reviewer_sended_reestNum)
    elif request.user.groups.filter(name='Руководитель').exists():
        group = 'Руководитель'
        remarkList = reestr.objects.filter(
            ((Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True)))
        IDlist = []
        for r in remarkList:
            IDlist.append(r.reestrID.id)
        reestrs = reestInfo.objects.filter(id__in=IDlist).exclude(status__in=excluded_status).annotate(
            reestr_priority_order=reestr_priority_order).order_by('reestr_priority_order', 'project_dogovor',
                                                                  'num_reestr')
        #reviewer_sended = len(reestInfo.objects.filter((Q(id__in=IDlist) & Q(status="На согласовании Рецензентом"))))
        reviewer_sended_reestNum = []
        #closed = len(reestInfo.objects.filter((Q(id__in=IDlist) & Q(status="Закрыт"))))
        closed = 0
        for r in reestrs:
            remarks_all = []
            for i in reestr.objects.filter((Q(reestrID=r.id) & (Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True))):
                remarks_all.append([i.id, i.num_remark, i.status, i.total_importance])
            remarks_all = np.array(remarks_all)
            if r.status == "На согласовании Рецензентом":
                full_remarks = []
                for i in reestr.objects.filter((Q(reestrID=r.id) & Q(actuality=True))):
                    full_remarks.append([i.id, i.num_remark, i.status, i.total_importance])
                full_remarks = np.array(full_remarks)
                reviewed = True
                for re in full_remarks:
                    if re[2] not in ["На согласовании Рецензентом", "Замечание снято"]:
                        reviewed = False
                        break
                if reviewed:
                    reviewer_sended_reestNum.append(r)
            try:
                remarks, counts = np.unique(np.array(remarks_all[:, 1]), return_counts=True)  # всего, без дублирований
            except Exception:
                remarks = []
                counts = []
            uniq_row = []
            for i in range(len(counts)):
                if counts[i] > 1:
                    row_indices = np.where(remarks_all[:, 1] == remarks[i])[0]
                    importances = remarks_all[row_indices, 3]
                    comm_imp = ""
                    if 'Существенное' in importances:
                        comm_imp = "Существенное"
                    elif 'В компетенции Заказчика' in importances:
                        comm_imp = "В компетенции Заказчика"
                    elif 'Несущественное' in importances:
                        comm_imp = "Несущественное"
                    statuses = remarks_all[row_indices, 2]
                    comm_stat = "В работе"
                    if all(x == "Замечание снято" for x in statuses):
                        comm_stat = "Замечание снято"
                    elif all(x in ["Замечание снято", "На соглсовании Рецензентом", "Принято ГИПом"] for x in statuses):
                        comm_stat = "Ответ подготовлен"
                    remarks_all[row_indices, 3] = comm_imp
                    remarks_all[row_indices, 2] = comm_stat
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
                else:
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
            remarks = len(remarks)  # всего
            close = 0
            final = 0
            work = 0
            closeC = 0
            finalC = 0
            workC = 0
            closeS = 0
            finalS = 0
            workS = 0
            closeI = 0
            finalI = 0
            workI = 0
            customer = 0
            signific = 0
            insignific = 0
            for i in range(len(uniq_row)):
                if remarks_all[uniq_row[i], 3] == 'В компетенции Заказчика':
                    customer += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeC += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalC += 1
                    else:
                        work += 1  # в работе
                        workC += 1
                elif remarks_all[uniq_row[i], 3] == 'Существенное':
                    signific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeS += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalS += 1
                    else:
                        work += 1  # в работе
                        workS += 1
                elif remarks_all[uniq_row[i], 3] == 'Несущественное':
                    insignific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeI += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalI += 1
                    else:
                        work += 1  # в работе
                        workI += 1
                else:
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                    else:
                        work += 1  # в работе

            info.append([r.id, remarks, customer, signific, insignific, work, close, final,
                         round(final * 100.0 / remarks, 2) if remarks else 0,
                         workC, closeC, finalC,
                         round(finalC * 100.0 / customer, 2) if customer else 0,
                         workS, closeS, finalS,
                         round(finalS * 100.0 / signific, 2) if signific else 0,
                         workI, closeI, finalI,
                         round(finalI * 100.0 / insignific, 2) if insignific else 0])
        reviewer_sended = len(reviewer_sended_reestNum)
    elif request.user.groups.filter(name='Исполнитель').exists():
        group = 'Исполнитель'
        remarkList = reestr.objects.filter(((Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True)))
        IDlist = []
        for r in remarkList:
            IDlist.append(r.reestrID.id)
        reestrs = reestInfo.objects.filter(id__in=IDlist).exclude(status__in=excluded_status).annotate(
            reestr_priority_order=reestr_priority_order).order_by('reestr_priority_order', 'project_dogovor',
                                                                  'num_reestr')
        #reviewer_sended = len(reestInfo.objects.filter((Q(id__in=IDlist) & Q(status="На согласовании Рецензентом"))))
        reviewer_sended_reestNum = []
        #closed = len(reestInfo.objects.filter((Q(id__in=IDlist) & Q(status="Закрыт"))))
        closed = 0
        for r in reestrs:
            remarks_all = []
            for i in reestr.objects.filter((Q(reestrID=r.id) & (Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True))):
                remarks_all.append([i.id, i.num_remark, i.status, i.total_importance])
            remarks_all = np.array(remarks_all)
            if r.status == "На согласовании Рецензентом":
                full_remarks = []
                for i in reestr.objects.filter((Q(reestrID=r.id) & Q(actuality=True))):
                    full_remarks.append([i.id, i.num_remark, i.status, i.total_importance])
                full_remarks = np.array(full_remarks)
                reviewed = True
                for re in full_remarks:
                    if re[2] not in ["На согласовании Рецензентом", "Замечание снято"]:
                        reviewed = False
                        break
                if reviewed:
                    reviewer_sended_reestNum.append(r)
            try:
                remarks, counts = np.unique(np.array(remarks_all[:, 1]), return_counts=True)  # всего, без дублирований
            except Exception:
                remarks = []
                counts = []
            uniq_row = []
            for i in range(len(counts)):
                if counts[i] > 1:
                    row_indices = np.where(remarks_all[:, 1] == remarks[i])[0]
                    importances = remarks_all[row_indices, 3]
                    comm_imp = ""
                    if 'Существенное' in importances:
                        comm_imp = "Существенное"
                    elif 'В компетенции Заказчика' in importances:
                        comm_imp = "В компетенции Заказчика"
                    elif 'Несущественное' in importances:
                        comm_imp = "Несущественное"
                    statuses = remarks_all[row_indices, 2]
                    comm_stat = "В работе"
                    if all(x == "Замечание снято" for x in statuses):
                        comm_stat = "Замечание снято"
                    elif all(x in ["Замечание снято", "На соглсовании Рецензентом", "Принято ГИПом"] for x in statuses):
                        comm_stat = "Ответ подготовлен"
                    remarks_all[row_indices, 3] = comm_imp
                    remarks_all[row_indices, 2] = comm_stat
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
                else:
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
            remarks = len(remarks)  # всего
            close = 0
            final = 0
            work = 0
            closeC = 0
            finalC = 0
            workC = 0
            closeS = 0
            finalS = 0
            workS = 0
            closeI = 0
            finalI = 0
            workI = 0
            customer = 0
            signific = 0
            insignific = 0
            for i in range(len(uniq_row)):
                if remarks_all[uniq_row[i], 3] == 'В компетенции Заказчика':
                    customer += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeC += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalC += 1
                    else:
                        work += 1  # в работе
                        workC += 1
                elif remarks_all[uniq_row[i], 3] == 'Существенное':
                    signific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeS += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalS += 1
                    else:
                        work += 1  # в работе
                        workS += 1
                elif remarks_all[uniq_row[i], 3] == 'Несущественное':
                    insignific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeI += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalI += 1
                    else:
                        work += 1  # в работе
                        workI += 1
                else:
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                    else:
                        work += 1  # в работе

            info.append([r.id, remarks, customer, signific, insignific, work, close, final,
                         round(final * 100.0 / remarks, 2) if remarks else 0,
                         workC, closeC, finalC,
                         round(finalC * 100.0 / customer, 2) if customer else 0,
                         workS, closeS, finalS,
                         round(finalS * 100.0 / signific, 2) if signific else 0,
                         workI, closeI, finalI,
                         round(finalI * 100.0 / insignific, 2) if insignific else 0])
        reviewer_sended = len(reviewer_sended_reestNum)
    elif request.user.groups.filter(name='Наблюдатель').exists():
        group = 'Наблюдатель'
        reestrs = reestInfo.objects.all().exclude(status="Скрыт").annotate(
            reestr_priority_order=reestr_priority_order).order_by('reestr_priority_order', 'project_dogovor',
                                                                  'num_reestr')
        #reviewer_sended = len(reestInfo.objects.filter(Q(status="На согласовании Рецензентом")))
        reviewer_sended_reestNum = []
        closed = len(reestInfo.objects.filter(Q(status="Закрыт")))
        for r in reestrs:
            remarks_all = []
            for i in reestr.objects.filter((Q(reestrID=r.id) & Q(actuality=True))):
                remarks_all.append([i.id, i.num_remark, i.status, i.total_importance])
            remarks_all = np.array(remarks_all)
            if r.status == "На согласовании Рецензентом":
                reviewed = True
                for re in remarks_all:
                    if re[2] not in ["На согласовании Рецензентом", "Замечание снято"]:
                        reviewed = False
                        break
                if reviewed:
                    reviewer_sended_reestNum.append(r)
            try:
                remarks, counts = np.unique(np.array(remarks_all[:, 1]), return_counts=True)  # всего, без дублирований
            except Exception:
                remarks = []
                counts = []
            uniq_row = []
            for i in range(len(counts)):
                if counts[i] > 1:
                    row_indices = np.where(remarks_all[:, 1] == remarks[i])[0]
                    importances = remarks_all[row_indices, 3]
                    comm_imp = ""
                    if 'Существенное' in importances:
                        comm_imp = "Существенное"
                    elif 'В компетенции Заказчика' in importances:
                        comm_imp = "В компетенции Заказчика"
                    elif 'Несущественное' in importances:
                        comm_imp = "Несущественное"
                    statuses = remarks_all[row_indices, 2]
                    comm_stat = "В работе"
                    if all(x == "Замечание снято" for x in statuses):
                        comm_stat = "Замечание снято"
                    elif all(x in ["Замечание снято", "На соглсовании Рецензентом", "Принято ГИПом"] for x in statuses):
                        comm_stat = "Ответ подготовлен"
                    remarks_all[row_indices, 3] = comm_imp
                    remarks_all[row_indices, 2] = comm_stat
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
                else:
                    uniq_row.append(np.where(remarks_all[:, 1] == remarks[i])[0][0])
            remarks = len(remarks)  # всего
            close = 0
            final = 0
            work = 0
            closeC = 0
            finalC = 0
            workC = 0
            closeS = 0
            finalS = 0
            workS = 0
            closeI = 0
            finalI = 0
            workI = 0
            customer = 0
            signific = 0
            insignific = 0
            for i in range(len(uniq_row)):
                if remarks_all[uniq_row[i], 3] == 'В компетенции Заказчика':
                    customer += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeC += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalC += 1
                    else:
                        work += 1  # в работе
                        workC += 1
                elif remarks_all[uniq_row[i], 3] == 'Существенное':
                    signific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeS += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalS += 1
                    else:
                        work += 1  # в работе
                        workS += 1
                elif remarks_all[uniq_row[i], 3] == 'Несущественное':
                    insignific += 1
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                        closeI += 1
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                        finalI += 1
                    else:
                        work += 1  # в работе
                        workI += 1
                else:
                    if remarks_all[uniq_row[i], 2] in ['Ответ подготовлен', "Принято ГИПом",
                                                       "На согласовании Рецензентом"]:
                        close += 1  # ответ подготовлен
                    elif remarks_all[uniq_row[i], 2] == 'Замечание снято':
                        final += 1  # закрыты
                    else:
                        work += 1  # в работе

            info.append([r.id, remarks, customer, signific, insignific, work, close, final,
                         round(final * 100.0 / remarks, 2) if remarks else 0,
                         workC, closeC, finalC,
                         round(finalC * 100.0 / customer, 2) if customer else 0,
                         workS, closeS, finalS,
                         round(finalS * 100.0 / signific, 2) if signific else 0,
                         workI, closeI, finalI,
                         round(finalI * 100.0 / insignific, 2) if insignific else 0])
        reviewer_sended = len(reviewer_sended_reestNum)
    else:
        return redirect("accounts/login/?next=/")
    if request.method == 'POST':
        if request.POST.get('email'):
            return render(request, 'index.html',
                          {'reestrs': reestrs, 'group': group, 'info': info, 'department': department,
                           'reviewer_sended': reviewer_sended, 'closed': closed, 'worked': len(reestrs)-reviewer_sended-closed, 'reviewer_sended_reestNum': reviewer_sended_reestNum})
        elif request.POST.get('causes_downloader'):
            begin_date = request.POST.get("begin_date")
            end_date = request.POST.get("end_date")
            if begin_date != "" and end_date != "":
                name = xlslxCauseCreate(request, begin_date, end_date)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            else:
                return render(request, 'index.html',
                              {'reestrs': reestrs, 'group': group, 'info': info, 'department': department,
                               'reviewer_sended': reviewer_sended, 'closed': closed, 'worked': len(reestrs)-reviewer_sended-closed, 'reviewer_sended_reestNum': reviewer_sended_reestNum})
        else:
            name = xlslxCreate(request)
            file_path = MEDIA_ROOT + "\\Tables" + name
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            return response
    else:
        return render(request, 'index.html',
                      {'reestrs': reestrs, 'group': group, 'info': info, 'department': department,
                       'reviewer_sended': reviewer_sended, 'closed': closed, 'worked': len(reestrs)-reviewer_sended-closed, 'reviewer_sended_reestNum': reviewer_sended_reestNum})


def newReestr(request):
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(
            name='Наблюдатель').exists() or request.user.is_superuser:
        dogovors = []
        for i in contracts.objects.all():
            dogovors.append([i.customer.id, i.number, str(i.date), i.name, i.id, i.num_reestrs])
        dogovors.sort(key=lambda j: j[1])
        if request.method == 'POST':
            form = ReestrForm(request.POST, request.FILES or None)
            if form.is_valid():
                form.save(commit=False)
                sum = 0
                for upload in form.files.getlist("add_files"):
                    sum += upload.size
                if reestInfo.objects.filter((Q(project_dogovor=form.cleaned_data.get("project_dogovor")) & Q(
                        num_reestr=form.cleaned_data.get("num_reestr")))):
                    messages.error(request, "Реестр с таким номером уже существует")
                elif sum <= MAX_FILE_UPLOAD:
                    try:
                        new = form.save(commit=True)
                        new.reestr_index = new.project_dogovor.number + '_' + new.num_reestr
                        new.save()
                        contract = contracts.objects.get(id=new.project_dogovor.id)
                        contract.num_reestrs += 1
                        contract.save()
                        name = form.cleaned_data.get("file_name")
                        comment = form.cleaned_data.get("file_comment")
                        form.save_files(new, name, comment)
                        messages.success(request, "Реестр создан")
                    except Exception as error:
                        print(error)
                        messages.error(request, "Возникла ошибка")
                else:
                    messages.error(request,
                                   'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                       sum))
        else:
            form = ReestrForm()
        return render(request, 'newReestr.html', {'form': form, 'dogovors': dogovors, 'gip': request.user.id})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа, наблюдателя или администратора, чтобы увидеть эту страницу."})


# def dashboard(request):
#     if request.user.is_authenticated:
#         if request.user.groups.filter(name='ГИП').exists():
#             group = 'ГИП'
#         elif request.user.groups.filter(name='Руководитель').exists():
#             group = 'Руководитель'
#         elif request.user.groups.filter(name='Исполнитель').exists():
#             group = 'Исполнитель'
#         else:
#             group = "Наблюдатель"
#         depart = departments.objects.filter(user=request.user.id)
#         if len(depart) > 0:
#             depart = depart[0].department
#         else:
#             depart = "All"
#         return render(request, 'dashboard.html', {'form': DashboardForm(), 'group': group, 'depart': depart})
#     else:
#         return redirect("accounts/login/?next=/")


def infoGIP(request, id):
    reest = reestInfo.objects.get(id=id)
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(
            name='Наблюдатель').exists() or request.user.is_superuser:
        return render(request, 'reestInfo.html', {'reest': reest})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или администратора, чтобы увидеть эту страницу."})


def dynamic(request, id):
    if request.user.is_authenticated:
        # основные данные из БД
        reest = reestInfo.objects.get(id=id)
        remarks = reestr.objects.filter(reestrID=id).order_by('num_remark', 'remark_v')
        depart = []
        for r in remarks:
            if r.department is not None:
                depart.append(r.department)
        depart = np.unique(np.array(depart))
        # базовый график
        xpoints = [0, 1, 1.5, 2, 2.5, 3, 5, 6.25, 7.5, 8.75, 10, 12.5, 15]
        ypoints = [0, 1, 1.5, 2, 2.5, 3, 5, 6.25, 7.5, 8.75, 10, 12.5, 15]
        statuses = ["Формирование", "На заполнении ГИПом", "На заполнении руководителем", "На заполнении исполнителем",
                    "На согласовании руководителем", "На согласовании ГИПом", "Согласовано ГИПом", "Подготовка ответов",
                    "На согласовании руководителем", "На согласовании ГИПом", "Принято ГИПом",
                    "На согласовании Рецензентом", "Замечание снято"]
        dateLabels = [dateDBformat(reest.start_date), dateDBformat(workDays(reest.start_date, 1)), '',
                      dateDBformat(workDays(reest.start_date, 2)), '',
                      dateDBformat(workDays(reest.start_date, 3)), dateDBformat(workDays(reest.start_date, 5)), '', '',
                      '', dateDBformat(workDays(reest.start_date, 10)), '',
                      dateDBformat(workDays(reest.start_date, 15))]
        xpoints_remarks = []
        xlabels = []
        ypoints_remarks = []
        hover = []
        chosen_remarks = []
        # кнопки
        if request.method == 'POST':
            if request.POST.get('all'):
                for i in remarks:
                    chosen_remarks.append(i.id)
            elif request.POST.get('none'):
                chosen_remarks = []
            else:
                chosen_remarks = request.POST.getlist("remarks")
                for i in range(len(chosen_remarks)):
                    chosen_remarks[i] = int(chosen_remarks[i])
            if request.POST.get('dwnld') == "true":
                if len(chosen_remarks) == 0:
                    for i in remarks:
                        chosen_remarks.append(i.id)
                name = xlslxStatusCreate(request, chosen_remarks)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            else:
                for j in chosen_remarks:
                    xpoints_remarks.append([])
                    ypoints_remarks.append([])
                    xlabels.append([])
                    hover.append([])
                    for i in ChangeLog.objects.filter((Q(model="Замечания") & Q(object_id=j))).order_by('changed'):
                        try:  # для обхода ошибки в случае отсутствия статуса в списке изменяемых полей
                            if i.data["Статус"] == "Формирование":
                                ypoints_remarks[-1].append(0)
                            elif i.data["Статус"] == "На заполнении ГИПом":
                                ypoints_remarks[-1].append(1)
                            elif i.data["Статус"] == "На заполнении руководителем":
                                ypoints_remarks[-1].append(1.5)
                            elif i.data["Статус"] == "На заполнении исполнителем":
                                ypoints_remarks[-1].append(2)
                            elif i.data["Статус"] == "На согласовании руководителем" or i.data[
                                "Статус"] == "На доработке руководителем":
                                if ypoints_remarks[-1][-1] >= 5:
                                    ypoints_remarks[-1].append(7.5)
                                else:
                                    ypoints_remarks[-1].append(2.5)
                            elif i.data["Статус"] == "На согласовании ГИПом":
                                if ypoints_remarks[-1][-2] >= 5:
                                    ypoints_remarks[-1].append(8.75)
                                else:
                                    ypoints_remarks[-1].append(3)
                            elif i.data["Статус"] == "Согласовано ГИПом":
                                ypoints_remarks[-1].append(5)
                            elif i.data["Статус"] in ["Подготовка ответов исполнителем",
                                                      "Подготовка ответов руководителем", "Подготовка ответов ГИПом"]:
                                ypoints_remarks[-1].append(6.25)
                            elif i.data["Статус"] == "Принято ГИПом":
                                ypoints_remarks[-1].append(10)
                            elif i.data["Статус"] == "На согласовании Рецензентом":
                                ypoints_remarks[-1].append(12.5)
                            elif i.data["Статус"] == "Замечание снято":
                                ypoints_remarks[-1].append(15)
                            elif i.data["Статус"] == "На доработке ГИПом":
                                ypoints_remarks[-1].append(1)
                            elif i.data["Статус"] == "На доработке исполнителем":
                                if ypoints_remarks[-1][-1] > 6.25:
                                    ypoints_remarks[-1].append(6.25)
                                else:
                                    ypoints_remarks[-1].append(2)
                            else:
                                ypoints_remarks[-1].append(i.data["Статус"])
                            xpoints_remarks[-1].append(workDelay(reest.start_date, i.changed.date()))
                            xlabels[-1].append(dateDBformat(i.changed.date()))
                            hover[-1].append(i.user)
                        except Exception as e:
                            print("Статус не изменялся", e)
        # график
        px = 1 / plt.rcParams['figure.dpi']
        fig = plt.figure(figsize=(850 * px, 600 * px))
        plt.plot(xpoints, ypoints, marker='o', color='#9B9B9B')
        for i in range(len(xpoints_remarks)):
            plt.plot(xpoints_remarks[i], ypoints_remarks[i], marker='o')
            for j in range(len(xpoints_remarks[i])):
                if xpoints_remarks[i][j] not in xpoints:
                    xpoints.append(xpoints_remarks[i][j])
                    dateLabels.append(xlabels[i][j])
        legend = ['']
        for i in chosen_remarks:
            r = reestr.objects.get(id=i)
            legend.append(r.num_remark + '-' + str(r.remark_v))
        plt.legend(legend, ncol=2)
        plt.title("Динамика")
        plt.xlabel("Дата")
        plt.ylabel("Статус")
        plt.xticks(xpoints, dateLabels, rotation=90)
        plt.yticks(ypoints, statuses)
        plt.tight_layout()
        imgdata = StringIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)
        data = imgdata.getvalue()
        return render(request, 'dynamic.html',
                      {'reestrID': id, 'plot': data, 'remarks': remarks, 'reest': reest, 'departments': depart})
    else:
        return render(request, 'log_error.html', {'text': "Пожалуйста, авторизируйтесь."})

def spec_length(string_num):
    l = 0
    for i in string_num:
        if i in '0123456789':
            l += 1
        if i == '[':
            break
    return l

def date_formatting(d):
    result = ''
    if d.day < 10:
        result += '0'
    result += str(d.day) + '.'
    if d.month < 10:
        result += '0'
    result += str(d.month) +'.' + str(d.year)
    return result

def homeGIP(request, id):
    try:
        department = departments.objects.get(user=request.user.id).department
        subs = departments.objects.get(user=request.user.id).substitute.all()
    except Exception:
        department = ""
        subs = []
    subcontracts = User.objects.filter(groups__name='Субподрядчик')
    fact = ['', '', '', '', '', '']
    start_date = reestInfo.objects.get(id=id).start_date
    plan = [start_date, workDays(start_date, 2), workDays(start_date, 4), workDays(start_date, 9)]
    if reestInfo.objects.get(id=id).status == "Закрыт":
        try:
            closed = reestr.objects.filter((Q(reestrID=id) & Q(status="Замечание снято"))).order_by(
                '-cancel_remark_date')
            for i in closed:
                if i.cancel_remark_date is not None:
                    fact[4] = i.cancel_remark_date
                    break;
        except Exception as e:
            print(e)
    for i in ChangeLog.objects.filter((Q(model="Реестры") & Q(object_id=id))).order_by('changed'):
        try:
            if i.data["Статус"] == "На заполнении":
                fact[0] = i.changed.date()
            if i.data["old_Статус"] == "На заполнении":
                fact[1] = i.changed.date()
            if i.data["Статус"] == "Согласовано ГИПом":
                fact[2] = i.changed.date()
            if i.data["Статус"] == "На согласовании Рецензентом":
                fact[3] = i.changed.date()
            if i.data["Статус"] == "Закрыт" and fact[4] == '':
                fact[4] = i.changed.date()
        except Exception:
            print("Статус не изменён")
    for i in range(4):
        if fact[i] != '' and plan[i] - fact[i] < timedelta(0):
            delay = workDelay(plan[i], fact[i])
            fact[i] = date_formatting(fact[i]) + '(-' + str(delay) + ')'
            plan[i] = date_formatting(plan[i])
        elif fact[i] != '' and plan[i] - fact[i] > timedelta(0):
            delay = workDelay(fact[i], plan[i])
            fact[i] = date_formatting(fact[i]) + '(+' + str(delay) + ')'
            plan[i] = date_formatting(plan[i])
        elif fact[i] != '' and plan[i] - fact[i] == timedelta(0):
            fact[i] = date_formatting(fact[i])
            plan[i] = date_formatting(plan[i])
        elif fact[i] == '' and plan[i] - date.today() >= timedelta(0):
            delay = workDelay(date.today(), plan[i])
            plan[i] = date_formatting(plan[i]) + '(осталось дней: ' + str(delay) + ')'
        elif fact[i] == '' and plan[i] - date.today() < timedelta(0):
            delay = workDelay(plan[i], date.today())
            plan[i] = date_formatting(plan[i]) + '(задержано дней: ' + str(delay) + ')'
    if fact[4] != '':
        fact[4] = date_formatting(fact[4])
    if request.user.is_superuser:
        group = "Администратор"
        reest = reestInfo.objects.get(id=id)
        reestrs = reestr.objects.filter(reestrID=id).annotate(remark_priority_order=remark_priority_order,
                                                              custom_string_order=Length('num_remark')).order_by(
            'remark_priority_order', 'custom_string_order', 'num_remark')
        to_reviewer = len(reestr.objects.filter((Q(reestrID=id) & Q(status="На согласовании Рецензентом"))))
        answered = len(reestr.objects.filter((Q(reestrID=id) & Q(status="Принято ГИПом"))))
        closed = len(reestr.objects.filter((Q(reestrID=id) & Q(status="Замечание снято"))))
        max_remark_num = 0
        max_remark_point_num = 0
        for i in reestrs:
            if '.' not in i.num_remark:
                if len(i.num_remark) > max_remark_num:
                    max_remark_num = len(i.num_remark)
            else:
                point_idx = i.num_remark.find('.')
                if len(i.num_remark[:point_idx]) > max_remark_num:
                    max_remark_num = len(i.num_remark[:point_idx])
                if len(i.num_remark[point_idx + 1:]) > max_remark_point_num:
                    max_remark_point_num = len(i.num_remark[point_idx + 1:])
        dubl = []
        first_dubl = []
        uniq_nums, counts = np.unique(np.array([[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in reestr.objects.filter((Q(reestrID=id) & Q(actuality=True)))]), return_counts=True, axis=0)
        for i in uniq_nums[counts > 1]:
            buff_dubl = []
            for j in reestr.objects.filter((Q(reestrID=id) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4]))):
                buff_dubl.append(j.id)
            dubl.append(buff_dubl)
            first_dubl.append(np.min(np.array(buff_dubl)))
        dubl = [i for sublist in dubl for i in sublist]
        if request.method == 'POST':
            if request.POST.get('status'):
                reest.status = request.POST.get("status")
                step2 = True
                if request.POST.get("status") == "Подготовка ответов":
                    for r in reestrs:
                        r.deadline = workDays(date.today(), 4)
                        if r.executor_name.groups.filter(name='ГИП').exists():
                            r.status = "Подготовка ответов ГИПом"
                        if r.executor_name.groups.filter(name='Руководитель').exists():
                            r.status = "Подготовка ответов руководителем"
                        if r.executor_name.groups.filter(name='Исполнитель').exists():
                            r.status = "Подготовка ответов исполнителем"
                        r.save(update_fields=['status', 'deadline'])
                    reest.save(update_fields=['status'])
                    return redirect('uploadFile', reest.id)
                if request.POST.get("status") == "На согласовании рецензентом":
                    for r in reestrs:
                        if r.status == "Принято ГИПом":
                            r.status = "На согласовании Рецензентом"
                            r.save(update_fields=['status'])
                    reest.save(update_fields=['status'])
                    return redirect('uploadFile', reest.id)
                if request.POST.get("status") == "Формирование":
                    for r in reestrs:
                        if r.root_cause_list != "" and r.root_cause_list is not None:
                            r.status = "На согласовании ГИПом"
                        elif r.executor_name is not None:
                            r.status = "На заполнении исполнителем"
                            step2 = False
                        else:
                            r.status = "На заполнении руководителем"
                            step2 = False
                        r.deadline = workDays(date.today(), 1)
                        r.save(update_fields=['status', 'deadline'])
                    if step2:
                        reest.status = "На согласовании"
                    reest.save(update_fields=['status'])
            elif request.POST.get('actuality'):
                name = xlslxCreate(request, actual=False)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            else:
                name = xlslxCreate(request)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
    elif request.user.groups.filter(name='Наблюдатель').exists():
        group = "Наблюдатель"
        reest = reestInfo.objects.get(id=id)
        reestrs = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True))).annotate(
            remark_priority_order=remark_priority_order, custom_string_order=Length('num_remark')).order_by(
            'remark_priority_order', 'custom_string_order', 'num_remark')
        to_reviewer = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(status="На согласовании Рецензентом"))))
        answered = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(status="Принято ГИПом"))))
        closed = len(reestr.objects.filter((Q(reestrID=id)& Q(actuality=True) & Q(status="Замечание снято"))))
        max_remark_num = 0
        max_remark_point_num = 0
        for i in reestrs:
            if '.' not in i.num_remark:
                if len(i.num_remark) > max_remark_num:
                    max_remark_num = len(i.num_remark)
            else:
                point_idx = i.num_remark.find('.')
                if len(i.num_remark[:point_idx]) > max_remark_num:
                    max_remark_num = len(i.num_remark[:point_idx])
                if len(i.num_remark[point_idx + 1:]) > max_remark_point_num:
                    max_remark_point_num = len(i.num_remark[point_idx + 1:])
        dubl = []
        first_dubl = []
        uniq_nums, counts = np.unique(
            np.array([[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in reestrs]),
            return_counts=True, axis=0)
        for i in uniq_nums[counts > 1]:
            buff_dubl = []
            for j in reestr.objects.filter((Q(reestrID=id) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(
                    rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4]))):
                buff_dubl.append(j.id)
            dubl.append(buff_dubl)
            first_dubl.append(np.min(np.array(buff_dubl)))
        dubl = [i for sublist in dubl for i in sublist]
        if request.method == 'POST':
            if request.POST.get('status'):
                try:
                    name = xlslxCreate(request, userRole='Наблюдатель')
                    file_path = MEDIA_ROOT + "\\Tables" + name
                    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                    return response
                except Exception as e:
                    messages.success(request, e)
            elif request.POST.get('actuality'):
                name = xlslxCreate(request, actual=False)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            elif request.POST.get('id'):
                name = xlslxCreate(request)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
    elif request.user.groups.filter(name='ГИП').exists():
        group = "ГИП"
        remark_gip_priority_order = Case(
            When(Q(status="На заполнении ГИПом") & Q(gip=request.user), then=Value(1)),
            When(Q(status="На заполнении руководителем") & Q(responsibleTrouble_name=request.user), then=Value(2)),
            When(Q(status="На заполнении исполнителем") & Q(executor_name=request.user), then=Value(3)),
            When(Q(status="На доработке ГИПом") & Q(gip=request.user), then=Value(4)),
            When(Q(status="На доработке руководителем") & Q(responsibleTrouble_name=request.user), then=Value(5)),
            When(Q(status="На доработке исполнителем") & Q(executor_name=request.user), then=Value(6)),
            When(Q(status="На согласовании ГИПом") & Q(gip=request.user), then=Value(7)),
            When(Q(status="На согласовании руководителем") & Q(responsibleTrouble_name=request.user), then=Value(8)),
            When(Q(status="Подготовка ответов ГИПом") & Q(gip=request.user), then=Value(9)),
            When(Q(status="Подготовка ответов руководителем") & Q(responsibleTrouble_name=request.user),
                 then=Value(10)),
            When(Q(status="Подготовка ответов исполнителем") & Q(executor_name=request.user), then=Value(11)),
            When(Q(status="На заполнении исполнителем") & ~Q(executor_name=request.user), then=Value(12)),
            When(Q(status="На доработке исполнителем") & ~Q(executor_name=request.user), then=Value(13)),
            When(Q(status="Подготовка ответов исполнителем") & ~Q(executor_name=request.user), then=Value(14)),
            When(Q(status="На заполнении руководителем") & ~Q(responsibleTrouble_name=request.user), then=Value(15)),
            When(Q(status="На доработке руководителем") & ~Q(responsibleTrouble_name=request.user), then=Value(16)),
            When(Q(status="На согласовании руководителем") & ~Q(responsibleTrouble_name=request.user), then=Value(17)),
            When(Q(status="Подготовка ответов руководителем") & ~Q(responsibleTrouble_name=request.user),
                 then=Value(18)),
            When(Q(status="На заполнении ГИПом") & ~Q(gip=request.user), then=Value(19)),
            When(Q(status="На доработке ГИПом") & ~Q(gip=request.user), then=Value(20)),
            When(Q(status="На согласовании ГИПом") & ~Q(gip=request.user), then=Value(21)),
            When(Q(status="Подготовка ответов ГИПом") & ~Q(gip=request.user), then=Value(22)),
            When(status="На согласовании Рецензентом", then=Value(23)),
            When(status="Согласовано ГИПом", then=Value(24)),
            When(status="Принято ГИПом", then=Value(25)),
            When(status="Замечание снято", then=Value(26)),
            default=Value(-1)
        )
        reest = reestInfo.objects.get(id=id)
        if reest.gip == request.user or reest.gip in subs:
            reestrs = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True))).annotate(
                remark_priority_order=remark_priority_order, custom_string_order=Length('num_remark')).order_by(
                'remark_priority_order', 'custom_string_order', 'num_remark')
            to_reviewer = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(status="На согласовании Рецензентом"))))
            answered = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(status="Принято ГИПом"))))
            closed = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(status="Замечание снято"))))
        else:
            remarks = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs))))
            remarks_info = [[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in remarks]
            remarks_id = [i.id for i in remarks]
            for i in remarks_info:
                adding_remark = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4])))
                for j in adding_remark:
                    if j not in remarks:
                        remarks_id.append(j.id)
            reestrs = reestr.objects.filter(id__in=remarks_id).annotate(remark_priority_order=remark_gip_priority_order, custom_string_order=Length('num_remark')).order_by('remark_priority_order', 'custom_string_order', 'num_remark')
            to_reviewer = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="На согласовании Рецензентом"))))
            answered = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="Принято ГИПом"))))
            closed = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="Замечание снято"))))
        max_remark_num = 0
        max_remark_point_num = 0
        for i in reestrs:
            if '.' not in i.num_remark:
                if len(i.num_remark) > max_remark_num:
                    max_remark_num = len(i.num_remark)
            else:
                point_idx = i.num_remark.find('.')
                if len(i.num_remark[:point_idx]) > max_remark_num:
                    max_remark_num = len(i.num_remark[:point_idx])
                if len(i.num_remark[point_idx+1:]) > max_remark_point_num:
                    max_remark_point_num = len(i.num_remark[point_idx+1:])
        dubl = []
        first_dubl = []
        uniq_nums, counts = np.unique(
            np.array([[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in reestrs]),
            return_counts=True, axis=0)
        for i in uniq_nums[counts > 1]:
            buff_dubl = []
            for j in reestr.objects.filter((Q(reestrID=id) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(
                    rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4]))):
                buff_dubl.append(j.id)
            dubl.append(buff_dubl)
            first_dubl.append(np.min(np.array(buff_dubl)))
        dubl = [i for sublist in dubl for i in sublist]
        deadline = workDays(reest.start_date, 2)
        if request.method == 'POST':
            if request.POST.get('status_report'):
                try:
                    name = xlslxCreate(request, userRole='Наблюдатель')
                    file_path = MEDIA_ROOT + "\\Tables" + name
                    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                    return response
                except Exception as e:
                    messages.success(request, e)
            elif request.POST.get('status'):
                reest.status = request.POST.get("status")
                step2 = True
                if request.POST.get("status") == "Подготовка ответов":
                    mails = []
                    for r in reestrs:
                        r.deadline = workDays(date.today(), 4)
                        if r.executor_name == request.user:
                            r.status = "Подготовка ответов ГИПом"
                        elif r.executor_name == r.responsibleTrouble_name:
                            r.status = "Подготовка ответов руководителем"
                        else:
                            r.status = "Подготовка ответов исполнителем"
                        mails.append(r.executor_name.email)
                        r.save(update_fields=['status', 'deadline'])
                    reest.save(update_fields=['status'])
                    try:
                        message = reest.project_dogovor.number[4:9] + reest.num_reestr
                        email_sender(np.unique(np.array(mails)), message, reest.id)
                    except Exception:
                        print("Письма не отправлены")
                    return redirect('uploadFile', reest.id)
                if request.POST.get("status") == "На согласовании Рецензентом":
                    for r in reestrs:
                        if r.status == "Принято ГИПом":
                            r.status = "На согласовании Рецензентом"
                            r.save(update_fields=['status'])
                    reest.save(update_fields=['status'])
                    return render(request, 'homeGIP.html',
                                  {'reestrs': reestrs,
                       'reest': reest,
                       'deadline': deadline,
                       'group': group,
                       'dubl': dubl,
                       'first_dubl': first_dubl,
                       'subs': subs,
                        'to_reviewer': to_reviewer,
                        'answered': answered,
                        'closed': closed,
                        'worked': len(reestrs)-to_reviewer-answered-closed,
                        'max_remark_num': max_remark_num,
                        'max_remark_point_num': max_remark_point_num,
                        'subcontracts': subcontracts,
                        'fact': fact,
                        'plan': plan})
                mails = []
                if request.POST.get("status") == "Формирование":
                    reest.status = "На заполнении"
                    try:
                        for r in reestrs:
                            if r.status == "Формирование" or r.status == "На заполнении ГИПом":
                                if r.root_cause_list != "" and r.root_cause_list is not None:
                                    r.status = "На согласовании ГИПом"
                                elif r.executor_name is not None:
                                    r.status = "На заполнении исполнителем"
                                    mails.append(r.executor_name.email)
                                    step2 = False
                                else:
                                    r.status = "На заполнении руководителем"
                                    mails.append(r.responsibleTrouble_name.email)
                                    step2 = False
                                r.deadline = workDays(date.today(), 1)
                                r.save(update_fields=['status', 'deadline'])
                            elif r.status != "На согласовании ГИПом":
                                step2 = False
                        if step2:
                            reest.status = "На согласовании"
                            try:
                                message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                email_sender(reest.gip.email, message, reest.id)
                            except Exception as e:
                                messages.error(request, "Письма не отправлены " + str(e))
                        else:
                            try:
                                message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                email_sender(np.unique(np.array(mails)), message, reest.id)
                            except Exception as e:
                                messages.error(request, "Письма не отправлены " + str(e))
                        reest.save(update_fields=['status'])
                    except Exception as e:
                        messages.error(request, "Возникла ошибка " + str(e))

            elif request.POST.get('actuality'):
                name = xlslxCreate(request, actual=False)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            elif request.POST.get('autoExport'):
                f = files.objects.filter(
                    (Q(reestr=reest.id) & Q(file_name='Файл замечаний от ФАУ "Главгосэкспертиза России"')))[0].file
                name = auto_export(f, reest)
                # file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(name, 'rb'), as_attachment=True)
                return response
            elif request.POST.get('plannerCheck'):
                name = xlsxGIPplannerCheckCreate(request, reest)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            else:
                name = xlslxCreate(request)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
        return render(request, 'homeGIP.html',
                      {'reestrs': reestrs,
                       'reest': reest,
                       'deadline': deadline,
                       'group': group,
                       'dubl': dubl,
                       'first_dubl': first_dubl,
                       'subs': subs,
                        'to_reviewer': to_reviewer,
                        'answered': answered,
                        'closed': closed,
                        'worked': len(reestrs)-to_reviewer-answered-closed,
                        'max_remark_num': max_remark_num,
                        'max_remark_point_num': max_remark_point_num,
                        'subcontracts': subcontracts,
                        'fact': fact,
                        'plan': plan})
    elif request.user.groups.filter(name='Руководитель').exists():
        group = "Руководитель"
        remark_boss_priority_order = Case(
            When(Q(status="На заполнении руководителем") & Q(responsibleTrouble_name=request.user), then=Value(1)),
            When(Q(status="На заполнении исполнителем") & Q(executor_name=request.user), then=Value(2)),
            When(Q(status="На доработке руководителем") & Q(responsibleTrouble_name=request.user), then=Value(3)),
            When(Q(status="На доработке исполнителем") & Q(executor_name=request.user), then=Value(4)),
            When(Q(status="На согласовании руководителем") & Q(responsibleTrouble_name=request.user), then=Value(5)),
            When(Q(status="Подготовка ответов руководителем") & Q(responsibleTrouble_name=request.user), then=Value(6)),
            When(Q(status="Подготовка ответов исполнителем") & Q(executor_name=request.user), then=Value(7)),
            When(Q(status="На заполнении исполнителем") & ~Q(executor_name=request.user), then=Value(8)),
            When(Q(status="На доработке исполнителем") & ~Q(executor_name=request.user), then=Value(9)),
            When(Q(status="Подготовка ответов исполнителем") & ~Q(executor_name=request.user), then=Value(10)),
            When(Q(status="На заполнении руководителем") & ~Q(responsibleTrouble_name=request.user), then=Value(11)),
            When(Q(status="На доработке руководителем") & ~Q(responsibleTrouble_name=request.user), then=Value(12)),
            When(Q(status="На согласовании руководителем") & ~Q(responsibleTrouble_name=request.user), then=Value(13)),
            When(Q(status="Подготовка ответов руководителем") & ~Q(responsibleTrouble_name=request.user),
                 then=Value(14)),
            When(status="На заполнении ГИПом", then=Value(15)),
            When(status="На доработке ГИПом", then=Value(16)),
            When(status="На согласовании ГИПом", then=Value(17)),
            When(status="Подготовка ответов ГИПом", then=Value(18)),
            When(status="На согласовании Рецензентом", then=Value(19)),
            When(status="Согласовано ГИПом", then=Value(20)),
            When(status="Принято ГИПом", then=Value(21)),
            When(status="Замечание снято", then=Value(22)),
            default=Value(-1)
        )
        reest = reestInfo.objects.get(id=id)
        remarks = reestr.objects.filter((Q(reestrID=id) & (Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True)))
        remarks_info = [[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in remarks]
        remarks_id = [i.id for i in remarks]
        for i in remarks_info:
            adding_remark = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4])))
            for j in adding_remark:
                if j not in remarks:
                    remarks_id.append(j.id)
        reestrs = reestr.objects.filter(id__in=remarks_id).annotate(remark_priority_order=remark_boss_priority_order, custom_string_order=Length('num_remark')).order_by('remark_priority_order',
                                                                                          'custom_string_order',
                                                                                          'num_remark')
        print(remarks_id)

        to_reviewer = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (
                    Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="На согласовании Рецензентом"))))
        answered = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (
                    Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="Принято ГИПом"))))
        closed = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (
                    Q(responsibleTrouble_name=request.user) | Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="Замечание снято"))))
        max_remark_num = 0
        max_remark_point_num = 0
        for i in reestrs:
            if '.' not in i.num_remark:
                if len(i.num_remark) > max_remark_num:
                    max_remark_num = len(i.num_remark)
            else:
                point_idx = i.num_remark.find('.')
                if len(i.num_remark[:point_idx]) > max_remark_num:
                    max_remark_num = len(i.num_remark[:point_idx])
                if len(i.num_remark[point_idx + 1:]) > max_remark_point_num:
                    max_remark_point_num = len(i.num_remark[point_idx + 1:])
        dubl = []
        first_dubl = []
        uniq_nums, counts = np.unique(
            np.array([[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in reestrs]),
            return_counts=True, axis=0)
        for i in uniq_nums[counts > 1]:
            buff_dubl = []
            for j in reestr.objects.filter((Q(reestrID=id) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(
                    rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4]))):
                buff_dubl.append(j.id)
            dubl.append(buff_dubl)
            first_dubl.append(np.min(np.array(buff_dubl)))
        dubl = [i for sublist in dubl for i in sublist]
        if request.method == 'POST':
            if request.POST.get('actuality'):
                name = xlslxCreate(request, actual=False)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            elif request.POST.get('id'):
                name = xlslxCreate(request, 'Руководитель')
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
    elif request.user.groups.filter(name='Исполнитель').exists():
        group = "Исполнитель"
        reest = reestInfo.objects.get(id=id)
        remarks = reestr.objects.filter((Q(reestrID=id) & (Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(actuality=True)))
        remarks_info = [[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in remarks]
        remarks_id = [i.id for i in remarks]
        for i in remarks_info:
            adding_remark = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & Q(num_remark=i[0]) & Q(
                remark_name=i[1]) & Q(rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4])))
            for j in adding_remark:
                if j not in remarks:
                    remarks_id.append(j.id)
        reestrs = reestr.objects.filter(id__in=remarks_id).annotate(remark_priority_order=remark_employee_priority_order, custom_string_order=Length('num_remark')).order_by('remark_priority_order', 'custom_string_order', 'num_remark')
        to_reviewer = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="На согласовании Рецензентом"))))
        answered = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="Принято ГИПом"))))
        closed = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) & (Q(executor_name=request.user) | Q(responsibleTrouble_name__in=subs) | Q(executor_name__in=subs)) & Q(status="Замечание снято"))))
        max_remark_num = 0
        max_remark_point_num = 0
        for i in reestrs:
            if '.' not in i.num_remark:
                if len(i.num_remark) > max_remark_num:
                    max_remark_num = len(i.num_remark)
            else:
                point_idx = i.num_remark.find('.')
                if len(i.num_remark[:point_idx]) > max_remark_num:
                    max_remark_num = len(i.num_remark[:point_idx])
                if len(i.num_remark[point_idx + 1:]) > max_remark_point_num:
                    max_remark_point_num = len(i.num_remark[point_idx + 1:])
        dubl = []
        first_dubl = []
        uniq_nums, counts = np.unique(
            np.array([[i.num_remark, i.remark_name, i.rational, i.designation_name, i.section_name] for i in reestrs]),
            return_counts=True, axis=0)
        for i in uniq_nums[counts > 1]:
            buff_dubl = []
            for j in reestr.objects.filter((Q(reestrID=id) & Q(num_remark=i[0]) & Q(remark_name=i[1]) & Q(
                    rational=i[2]) & Q(designation_name=i[3]) & Q(section_name=i[4]))):
                buff_dubl.append(j.id)
            dubl.append(buff_dubl)
            first_dubl.append(np.min(np.array(buff_dubl)))
        dubl = [i for sublist in dubl for i in sublist]
        if request.method == 'POST':
            if request.POST.get('actuality'):
                name = xlslxCreate(request, actual=False)
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
            elif request.POST.get('id'):
                name = xlslxCreate(request, 'Исполнитель')
                file_path = MEDIA_ROOT + "\\Tables" + name
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                return response
    else:
        return render(request, 'log_error.html', {'text': "Пожалуйста, авторизируйтесь, чтобы увидеть эту страницу."})
    return render(request, 'homeGIP.html', {'reestrs': reestrs,
                                            'reest': reest,
                                            'group': group,
                                            'dubl': dubl,
                                            'first_dubl': first_dubl,
                                            'subs': subs,
                                            'to_reviewer': to_reviewer,
                                            'answered': answered,
                                            'closed': closed,
                                            'worked': len(reestrs)-to_reviewer-answered-closed,
                                            'max_remark_num': max_remark_num,
                                            'max_remark_point_num': max_remark_point_num,
                                            'subcontracts': subcontracts,
                                            'fact': fact,
                                            'plan': plan})


def fileManage(request, id):
    reest = reestInfo.objects.get(id=id)
    add_files = files.objects.filter(reestr_id=id)
    file_links = []
    for f in add_files:
        file_links.append("http://127.0.0.1:8000/media/" + str(f.file))
    if request.user.groups.filter(name='ГИП').exists() or request.user.is_superuser:
        if request.method == 'POST':
            if request.POST.get('deletelist'):
                delets = request.POST.get('deletelist')
                filelist = []
                k = 0
                while delets[0] not in '0123456789':
                    delets = delets[1:]
                for i in range(len(delets)):
                    if delets[i] == ",":
                        filelist.append(int(delets[k:i]))
                        k = i + 1
                    elif i == len(delets) - 1:
                        filelist.append(int(delets[k:]))
                for f in filelist:
                    files.objects.get(id=f).delete()
                add_files = files.objects.filter(reestr_id=id)
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
            elif request.POST.get('file_path'):
                response = FileResponse(open(MEDIA_ROOT + "/" + request.POST.get('file_path'), 'rb'),
                                        as_attachment=True)
                return response
            elif request.POST.get('downloadlist'):
                response = []
                for f in add_files:
                    response.append(MEDIA_ROOT + "/" + str(f.file))
                print(response)
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
            else:
                print("nothing")
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
        else:
            return render(request, 'fileManage.html',
                          {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
    elif request.user.groups.filter(name='Руководитель').exists():
        if request.method == 'POST':
            if request.POST.get('file_path'):
                response = FileResponse(open(MEDIA_ROOT + "/" + request.POST.get('file_path'), 'rb'),
                                        as_attachment=True)
                return response
            elif request.POST.get('downloadlist'):
                response = []
                for f in add_files:
                    response.append(MEDIA_ROOT + "/" + str(f.file))
                print(response)
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
            else:
                print("nothing")
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
        return render(request, 'fileManage.html',
                      {'reest': reest, 'files': add_files, 'group': 'Руководитель', 'file_links': file_links})
    elif request.user.groups.filter(name='Исполнитель').exists():
        if request.method == 'POST':
            if request.POST.get('file_path'):
                response = FileResponse(open(MEDIA_ROOT + "/" + request.POST.get('file_path'), 'rb'),
                                        as_attachment=True)
                return response
            elif request.POST.get('downloadlist'):
                response = []
                for f in add_files:
                    response.append(MEDIA_ROOT + "/" + str(f.file))
                print(response)
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
            else:
                print("nothing")
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
        return render(request, 'fileManage.html',
                      {'reest': reest, 'files': add_files, 'group': 'Исполнитель', 'file_links': file_links})
    elif request.user.groups.filter(name='Наблюдатель').exists():
        if request.method == 'POST':
            if request.POST.get('file_path'):
                response = FileResponse(open(MEDIA_ROOT + "/" + request.POST.get('file_path'), 'rb'),
                                        as_attachment=True)
                return response
            elif request.POST.get('downloadlist'):
                response = []
                for f in add_files:
                    response.append(MEDIA_ROOT + "/" + str(f.file))
                print(response)
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
            else:
                print("nothing")
                return render(request, 'fileManage.html',
                              {'reest': reest, 'files': add_files, 'group': 'ГИП', 'file_links': file_links})
        return render(request, 'fileManage.html',
                      {'reest': reest, 'files': add_files, 'group': 'Наблюдатель', 'file_links': file_links})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь, чтобы увидеть эту страницу."})


def delete_file(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.is_superuser:
        fileName = files.objects.get(id=id)
        if request.method == 'POST':
            reestr_id = files.objects.get(id=id).reestr_id
            files.objects.get(id=id).delete()
            return redirect('fileManage', id=reestr_id)
        else:
            return render(request, 'deleteFile.html', {'file': fileName})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или администратора, чтобы увидеть эту страницу."})


def delete_all(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.is_superuser:
        fileNames = files.objects.filter(reestr=id)
        reestr = reestInfo.objects.get(id=id)
        if request.method == 'POST':
            for f in fileNames:
                f.delete()
            return redirect('fileManage', id=id)
        else:
            return render(request, 'deleteAll.html', {'files': fileNames, 'reestr': reestr})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или администратора, чтобы увидеть эту страницу."})


def upload_file(request, id):
    if request.user.groups.filter(name='Руководитель').exists():
        group = "Руководитель"
    elif request.user.groups.filter(name='Исполнитель').exists():
        group = "Исполнитель"
    else:
        group = "ГИП"
    reestr = reestInfo.objects.get(id=id)
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES or None)
        if form.is_valid():
            form.save(commit=False)
            name = form.cleaned_data.get("file_name")
            comment = form.cleaned_data.get("comment")
            sum = 0
            for upload in form.files.getlist("file"):
                sum += upload.size
            if sum > MAX_FILE_UPLOAD:
                messages.error(request,
                               'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                   sum))
            else:
                try:
                    form.save_files(reestr, name, comment)
                    messages.success(request, 'Файлы успешно загружены')
                except Exception:
                    messages.error(request, 'Возникла ошибка')
    else:
        form = FileForm()
    return render(request, 'uploadFile.html', {'form': form, 'reestr': reestr, 'group': group})


def gip(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(
            name='Наблюдатель').exists() or request.user.is_superuser:
        reest = reestInfo.objects.get(id=id)
        endDate = reest.end_date - timedelta(days=1)
        if request.user.groups.filter(name='Наблюдатель').exists():
            role = "viewer"
        else:
            role = "GIP"
        if request.method == 'POST':
            form = GIPform(reest, request.POST, request.FILES or None)
            if form.is_valid():
                respons2 = request.POST.getlist('responsibleTrouble_name')
                sum = 0
                for upload in form.files.getlist("add_files"):
                    sum += upload.size
                if len(respons2) > 1:
                    respons = []
                    for i in range(len(respons2)):
                        respons.append(int(respons2[i]))
                    respons = np.unique(np.array(respons))
                    if len(respons) < len(respons2):
                        form.add_error('responsibleTrouble_name',
                                       'Ответственные за устранение замечаний не должны повторяться')
                    if sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    if len(respons) == len(respons2) and sum <= MAX_FILE_UPLOAD:
                        try:
                            for i in range(len(respons)):
                                if reestr.objects.filter((Q(responsibleTrouble_name=User.objects.get(id=respons[i])) &
                                                          Q(remark_v=form.cleaned_data.get("remark_v")) &
                                                          Q(num_remark=form.cleaned_data.get("num_remark")) &
                                                          Q(reestrID=form.cleaned_data.get("reestrID")) &
                                                          Q(remark_name=form.cleaned_data.get("remark_name")) &
                                                          Q(rational=form.cleaned_data.get("rational")) &
                                                          Q(designation_name=form.cleaned_data.get(
                                                              "designation_name")) &
                                                          Q(section_name=form.cleaned_data.get("section_name")))):
                                    messages.error(request, "Замечание уже существует")
                                else:
                                    name = form.cleaned_data.get("file_name")
                                    file_comment = form.cleaned_data.get("file_comment")
                                    new = form.save(commit=False)
                                    new.pk = None
                                    if form.cleaned_data.get("comment") != "":
                                        d = datetime.now()
                                        new.comment = (
                                                    form.cleaned_data.get("comment") + " (" + str(d.hour) + ':' + str(
                                                d.minute) +
                                                    ':' + str(d.second) + ' ' + str(d.day) + '.' + str(d.month) +
                                                    '.' + str(d.year) + ' ' + shortName(request.user) + ")")
                                    new = form.save(commit=True)
                                    new.responsibleTrouble_name = User.objects.get(id=respons[i])
                                    new.department = departments.objects.get(user=respons[i]).department
                                    new.remark_index = new.reestrID.reestr_index + '_' + new.num_remark + '_' + str(
                                        new.remark_v) + '_' + str(respons[i])
                                    if reest.status != "Формирование":
                                        new.status = "На заполнении руководителем"
                                    new.save(
                                        update_fields=['responsibleTrouble_name', 'comment', 'department', 'status',
                                                       'remark_index'])
                                    form.save_files(reestr=reest,
                                                    name=name,
                                                    comment=file_comment,
                                                    cause_name="",
                                                    cause_comment="",
                                                    remark=form.cleaned_data.get("num_remark"))
                                    messages.success(request, "Замечание создано")
                        except Exception as e:
                            messages.error(request, "Возникла ошибка " + str(e))
                else:
                    respons = form.cleaned_data.get('responsibleTrouble_name')
                    try:
                        if reestr.objects.filter((Q(responsibleTrouble_name=respons) &
                                                  Q(remark_v=form.cleaned_data.get("remark_v")) &
                                                  Q(num_remark=form.cleaned_data.get("num_remark")) &
                                                  Q(reestrID=form.cleaned_data.get("reestrID")) &
                                                  Q(remark_name=form.cleaned_data.get("remark_name")) &
                                                  Q(rational=form.cleaned_data.get("rational")) &
                                                  Q(designation_name=form.cleaned_data.get("designation_name")) &
                                                  Q(section_name=form.cleaned_data.get("section_name")))):
                            messages.error(request, "Замечание уже существует")
                        else:
                            if role != "viewer" and respons is None:
                                form.add_error('responsibleTrouble_name',
                                               'Пожалуйста, внесите данные')
                            if sum > MAX_FILE_UPLOAD:
                                messages.error(request,
                                               'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                                   sum))
                            if sum <= MAX_FILE_UPLOAD and (respons is not None or role == "viewer"):
                                new = form.save(commit=False)
                                if form.cleaned_data.get("comment") != "":
                                    d = datetime.now()
                                    new.comment = (form.cleaned_data.get("comment") + " (" + str(d.hour) + ':' + str(
                                        d.minute) +
                                                   ':' + str(d.second) + ' ' + str(d.day) + '.' + str(d.month) +
                                                   '.' + str(d.year) + ' ' + shortName(request.user) + ")")
                                if role != "viewer" and respons is not None:
                                    new.department = departments.objects.get(
                                        user=new.responsibleTrouble_name).department
                                if reest.status != "Формирование":
                                    new.status = "На заполнении руководителем"
                                if role == "viewer":
                                    new.status = "На заполнении ГИПом"
                                if respons is not None:
                                    new.remark_index = new.reestrID.reestr_index + '_' + new.num_remark + '_' + str(
                                        new.remark_v) + '_' + str(new.responsibleTrouble_name.id)
                                new.save()
                                name = form.cleaned_data.get("file_name")
                                file_comment = form.cleaned_data.get("file_comment")
                                form.save_files(reestr=reest,
                                                name=name,
                                                comment=file_comment,
                                                cause_name="",
                                                cause_comment="",
                                                remark=form.cleaned_data.get("num_remark"))
                                messages.success(request, "Замечание создано")
                    except Exception as e:
                        messages.error(request, "Возникла ошибка " + str(e))
            else:
                print(form.errors)
        else:
            form = GIPform(reest)
        return render(request, 'GIP.html', {'form': form,
                                            'gipcontext': reest.gip.last_name + ' ' + reest.gip.first_name,
                                            'reestrID': reest.id,
                                            'customer': reest.customer.name,
                                            'contract_number': reest.project_dogovor.number,
                                            'reviewer': reest.project_reviewer.name,
                                            'start_date': str(reest.start_date.year) + (
                                                '-' if reest.start_date.month > 9 else '-0') + str(
                                                reest.start_date.month) + (
                                                              '-' if reest.start_date.day > 9 else '-0') + str(
                                                reest.start_date.day),
                                            'end_date': str(endDate.year) + ('-' if endDate.month > 9 else '-0') + str(
                                                endDate.month) + ('-' if endDate.day > 9 else '-0') + str(endDate.day),
                                            'role': role,
                                            })
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа, наблюдателя или администратора, чтобы увидеть эту страницу."})


def gip1(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.is_superuser:
        remark = reestr.objects.get(id=id)
        reest = reestInfo.objects.get(id=remark.reestrID.id)
        endDate = reest.end_date - timedelta(days=1)
        next_remark = reestr.objects.filter((Q(reestrID=remark.reestrID) & Q(responsibleTrouble_name=None) & ~Q(id=id)))
        check_boss = 0
        if request.method == 'POST':
            if request.POST.get('remove_remark'):
                reestr.objects.get(id=id).delete()
                return redirect('homeGIP', id=reest.id)
            else:
                form = GIPform1(remark, request.POST, request.FILES or None)
                if form.is_valid():
                    respons2 = request.POST.getlist('responsibleTrouble_name')
                    sum = 0
                    for upload in form.files.getlist("add_files"):
                        sum += upload.size
                    if len(respons2) > 1:
                        respons = []
                        for i in range(len(respons2)):
                            respons.append(int(respons2[i]))
                            try:
                                check_boss += len(reestr.objects.filter(
                                    remark_index=reest.reestr_index + '_' + remark.num_remark + '_' + str(
                                        remark.remark_v) + '_' + str(respons[i])))
                                print(reestr.objects.filter(
                                    remark_index=reest.reestr_index + '_' + remark.num_remark + '_' + str(
                                        remark.remark_v) + '_' + str(respons[i])))
                            except Exception:
                                check_boss += 0
                        respons = np.unique(np.array(respons))
                        if len(respons) < len(respons2):
                            form.add_error('responsibleTrouble_name',
                                           'Ответственные за устранение замечаний не должны повторяться')
                        if sum > MAX_FILE_UPLOAD:
                            messages.error(request,
                                           'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                               sum))
                        if check_boss > 0:
                            messages.error(request,
                                           'Данное замечание уже назначено одному из выбранных исполнителей, выберите другого ответственного или удалите замечание кнопкой внизу страницы.')
                        if len(respons) == len(respons2) and sum <= MAX_FILE_UPLOAD and check_boss == 0:
                            try:
                                for i in range(len(respons)):
                                    if i > 0:
                                        if reest.status != "Формирование":
                                            stat = "На заполнении руководителем"
                                        else:
                                            stat = "На заполнении ГИПом"
                                        reestr.objects.create(reestrID=reest,
                                                              customer=reest.customer,
                                                              project_dogovor=reest.project_dogovor,
                                                              project_date_contract=reest.project_date_contract,
                                                              project_name=reest.project_name,
                                                              gip=reest.gip,
                                                              project_reviewer=reest.project_reviewer,
                                                              out_mail_num=reest.out_mail_num,
                                                              out_mail_date=reest.out_mail_date,
                                                              in_mail_num=reest.in_mail_num,
                                                              in_mail_date=reest.in_mail_date,
                                                              num_reestr=reest.num_reestr,
                                                              num_remark=remark.num_remark,
                                                              designation_name=remark.designation_name,
                                                              section_name=remark.section_name,
                                                              remark_name=remark.remark_name,
                                                              rational=remark.rational,
                                                              comment=remark.comment,
                                                              answer_remark=remark.answer_remark,
                                                              responsibleTrouble_name=User.objects.get(id=respons[i]),
                                                              department=departments.objects.get(
                                                                  user=respons[i]).department,
                                                              status=stat,
                                                              remark_index=reest.reestr_index + '_' + remark.num_remark + '_' + str(
                                                                  remark.remark_v) + '_' + str(respons[i]),
                                                              remark_v=0, )
                                    else:
                                        remark.responsibleTrouble_name = User.objects.get(id=respons[i])
                                        remark.department = departments.objects.get(
                                            user=remark.responsibleTrouble_name).department
                                        if reest.status != "Формирование":
                                            remark.status = "На заполнении руководителем"
                                        if form.cleaned_data.get("comment") != remark.comment and form.cleaned_data.get(
                                                "comment") != "":
                                            remark.comment = form.cleaned_data.get("comment") + " (" + str(
                                                datetime.now().hour) + ':' + str(datetime.now().minute) + ':' + str(
                                                datetime.now().second) + ' ' + str(datetime.now().day) + '.' + str(
                                                datetime.now().month) + '.' + str(datetime.now().year) + ' ' + shortName(
                                                request.user) + ")"
                                        remark.answer_remark = form.cleaned_data.get("answer_remark")
                                        remark.remark_index = reest.reestr_index + '_' + remark.num_remark + '_' + str(
                                            remark.remark_v) + '_' + str(respons[i])
                                        remark.save(
                                            update_fields=['responsibleTrouble_name', 'status', 'comment', 'answer_remark',
                                                           'department', 'remark_index'])
                                        name = form.cleaned_data.get("file_name")
                                        file_comment = form.cleaned_data.get("file_comment")
                                        form.save_files(reestr=reest,
                                                        name=name,
                                                        comment=file_comment,
                                                        cause_name="",
                                                        cause_comment="",
                                                        remark=form.cleaned_data.get("num_remark"))
                                    if reest.status != "Формирование" and User.objects.get(id=respons[i]) != request.user:
                                        #отправка письма при доработке от рецензента
                                        message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                        email_sender(User.objects.get(id=respons[i]).email, message, reest.id)
                                    messages.success(request, "Замечание создано")
                            except Exception as e:
                                print(e)
                                messages.error(request, "Возникла ошибка " + str(e))
                    else:
                        respons = form.cleaned_data.get('responsibleTrouble_name')
                        try:
                            check_boss = len(reestr.objects.filter(remark_index=reest.reestr_index + '_' + remark.num_remark + '_' + str(
                                    remark.remark_v) + '_' + str(respons.id)))
                        except Exception:
                            check_boss = 0
                        if check_boss > 0:
                            messages.error(request, 'Данное замечание уже назначено выбранному исполнителю, выберите другого ответственного или удалите замечание кнопкой внизу страницы.')
                        if sum <= MAX_FILE_UPLOAD and check_boss == 0:
                            try:
                                remark.responsibleTrouble_name = respons
                                remark.department = departments.objects.get(user=respons).department
                                remark.remark_index = reest.reestr_index + '_' + remark.num_remark + '_' + str(
                                    remark.remark_v) + '_' + str(respons.id)
                                if reest.status != "Формирование":
                                    remark.status = "На заполнении руководителем"
                                    if respons != request.user:
                                        #отправка письма при доработке от рецензента
                                        message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                        email_sender(respons.email, message, reest.id)
                                if remark.comment != form.cleaned_data.get("comment") and form.cleaned_data.get(
                                        "comment") != "":
                                    d = datetime.now()
                                    remark.comment = (
                                            form.cleaned_data.get("comment") + " (" + str(d.hour) + ':' + str(d.minute) +
                                            ':' + str(d.second) + ' ' + str(d.day) + '.' + str(d.month) +
                                            '.' + str(d.year) + ' ' + shortName(request.user) + ")")
                                remark.answer_remark = form.cleaned_data.get("answer_remark")
                                remark.save(update_fields=['responsibleTrouble_name', 'status', 'comment', 'answer_remark',
                                                           'department', 'remark_index'])
                                name = form.cleaned_data.get("file_name")
                                file_comment = form.cleaned_data.get("file_comment")
                                form.save_files(reestr=reest,
                                                name=name,
                                                comment=file_comment,
                                                cause_name="",
                                                cause_comment="",
                                                remark=form.cleaned_data.get('num_remark'))
                                messages.success(request, "Замечание создано")
                            except Exception:
                                messages.error(request, "Возникла ошибка")
                        if sum > MAX_FILE_UPLOAD:
                            messages.error(request,
                                           'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                               sum))
        else:
            form = GIPform1(remark)
        return render(request, 'GIP1.html', {'form': form,
                                             'gipcontext': reest.gip.last_name + ' ' + reest.gip.first_name,
                                             'customer': reest.customer.name,
                                             'contract_number': reest.project_dogovor.number,
                                             'reviewer': reest.project_reviewer.name,
                                             'reestrID': reest.id,
                                             'reestStatus': reest.status,
                                             'check_boss': check_boss,
                                             'start_date': str(reest.start_date.year) + (
                                                 '-' if reest.start_date.month > 9 else '-0') + str(
                                                 reest.start_date.month) + (
                                                               '-' if reest.start_date.day > 9 else '-0') + str(
                                                 reest.start_date.day),
                                             'end_date': str(endDate.year) + ('-' if endDate.month > 9 else '-0') + str(
                                                 endDate.month) + ('-' if endDate.day > 9 else '-0') + str(endDate.day),
                                             'next_remark': next_remark[0].id if len(next_remark) > 0 else id})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или администратора, чтобы увидеть эту страницу."})


def boss(request, id):
    if request.user.groups.filter(name='Руководитель').exists() or request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(name='Исполнитель').exists():
        db_form = reestr.objects.get(id=id)
        reest = reestInfo.objects.get(id=db_form.reestrID.id)
        endDate = reest.end_date - timedelta(days=1)
        try:
            subs = departments.objects.get(user=request.user.id).substitute.all()
        except Exception:
            subs = []
        if request.method == 'POST':
            if request.POST.get('executor_name'):
                form = BossForm1(db_form, request.POST or None)
                if form.is_valid():
                    executor_fail_name = form.cleaned_data.get('executor_fail_name')
                    executor_fail_text = form.cleaned_data.get('executor_fail_text')
                    db_form.executor_name = form.cleaned_data.get('executor_name')
                    if (
                            executor_fail_name is not None and executor_fail_name.id == emptyUserID and executor_fail_text != "") or executor_fail_name is None or executor_fail_name.id != emptyUserID:
                        try:
                            db_form.executor_fail_name = executor_fail_name
                            db_form.executor_fail_text = executor_fail_text
                            if form.cleaned_data.get("comment") != db_form.comment and form.cleaned_data.get(
                                    "comment") != "":
                                d = datetime.now()
                                db_form.comment = form.cleaned_data.get("comment") + " (" + str(d.hour) + ':' + str(
                                    d.minute) + ':' + str(d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(
                                    d.year) + ' ' + shortName(request.user) + ")"
                            db_form.answer_remark = form.cleaned_data.get("answer_remark")
                            db_form.status = "На заполнении исполнителем"
                            db_form.save(
                                update_fields=['executor_fail_name', 'executor_name', 'executor_fail_text', 'status',
                                               'comment', 'answer_remark'])
                            remarks = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(actuality=True) & Q(
                                responsibleTrouble_name=db_form.responsibleTrouble_name)))
                            send = True
                            mails = []
                            for r in remarks:
                                if r.executor_name is None:
                                    send = False
                                    break
                                else:
                                    mails.append(r.executor_name.email)
                            if send:
                                message = db_form.project_dogovor.number[4:9] + db_form.num_reestr
                                email_sender(np.unique(np.array(mails)), message, db_form.reestrID.id)
                            messages.success(request, "Изменения сохранены")
                        except Exception as e:
                            messages.error(request, "Возникла ошибка " + str(e))
                    if executor_fail_name is not None and executor_fail_name.id == emptyUserID and executor_fail_text == "":
                        form.add_error('executor_fail_text', 'Пожалуйста, внесите данные')
                else:
                    executor_fail_name = form.cleaned_data.get('executor_fail_name')
                    executor_fail_text = form.cleaned_data.get('executor_fail_text')
                    if executor_fail_name is not None and executor_fail_name.id == emptyUserID and executor_fail_text == "":
                        form.add_error('executor_fail_text', 'Пожалуйста, внесите данные')
            else:
                form = BossForm1(reest=db_form)
                try:
                    if db_form.comment != request.POST.get('comment'):
                        d = datetime.now()
                        db_form.comment = (
                                    request.POST.get('comment') + " (" + str(d.hour) + ':' + str(d.minute) + ':' +
                                    str(d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(
                                d.year) + ' ' + shortName(request.user) + ")")
                        db_form.status = "На доработке ГИПом"
                        db_form.save(update_fields=['comment', 'status'])
                        form = BossForm1(reest=db_form)
                        messages.success(request, "Изменения сохранены")
                    else:
                        messages.error(request, "Внесите причину возврата в п. 10.3 Комментарии")
                except Exception as e:
                    messages.error(request, "Возникла ошибка " + str(e))
        else:
            form = BossForm1(reest=db_form)
        if request.user == db_form.executor_name or db_form.executor_name in subs:
            next_step_key = True
        else:
            next_step_key = False
        return render(request, 'boss.html', {'form': form,
                                             'gipcontext': db_form.gip.last_name + ' ' + db_form.gip.first_name,
                                             'rescontext': db_form.responsibleTrouble_name.last_name + ' ' + db_form.responsibleTrouble_name.first_name,
                                             'reestrID': db_form.reestrID,
                                             'remarkID': id,
                                             'customer': db_form.customer.name,
                                             'contract_number': db_form.project_dogovor.number,
                                             'reviewer': db_form.project_reviewer.name,
                                             'emptyUserID': emptyUserID,
                                             'start_date': str(reest.start_date.year) + (
                                                 '-' if reest.start_date.month > 9 else '-0') + str(
                                                 reest.start_date.month) + (
                                                               '-' if reest.start_date.day > 9 else '-0') + str(
                                                 reest.start_date.day),
                                             'end_date': str(endDate.year) + ('-' if endDate.month > 9 else '-0') + str(
                                                 endDate.month) + ('-' if endDate.day > 9 else '-0') + str(endDate.day),
                                             'subcontracts': [i.id for i in User.objects.filter(groups=4)],
                                             'next_step_key': next_step_key})
    else:
        return render(request, 'log_error.html',
                      {'text': "Пожалуйста, авторизируйтесь в качестве руководителя, чтобы увидеть эту страницу."})


def employee(request, id):
    if request.user.groups.filter(name='Исполнитель').exists() or request.user.groups.filter(
            name='Руководитель').exists() or request.user.groups.filter(name='ГИП').exists():
        db_form = reestr.objects.get(id=id)
        reest = reestInfo.objects.get(id=db_form.reestrID.id)
        endDate = reest.end_date - timedelta(days=1)
        try:
            subs = departments.objects.get(user=request.user.id).substitute.all()
        except Exception:
            subs = []
        if request.method == 'POST':
            form = emplForm(db_form, request.POST, request.FILES or None)
            if form.is_valid():
                form.save(commit=False)
                labor_costs_plan = form.cleaned_data.get('labor_costs_plan')
                d = datetime.now()
                if form.cleaned_data.get('comment') != db_form.comment and form.cleaned_data.get('comment') != "":
                    comment = form.cleaned_data.get('comment') + " (" + str(d.hour) + ':' + str(d.minute) + ':' + str(
                        d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(d.year) + ' ' + shortName(
                        request.user) + ")"
                else:
                    comment = db_form.comment
                answer_remark = form.cleaned_data.get('answer_remark')
                total_importance = form.cleaned_data.get('total_importance')
                root_cause_list = form.cleaned_data.get('root_cause_list')
                root_cause_text = form.cleaned_data.get('root_cause_text')
                answer_date = form.cleaned_data.get('answer_date_plan')
                answer_deadline = form.cleaned_data.get('answer_deadline_correct_plan')
                root_cause_comment = form.cleaned_data.get('root_cause_comment')
                importance1 = form.cleaned_data.get('importance1')
                importance2 = form.cleaned_data.get('importance2')
                importance3 = form.cleaned_data.get('importance3')
                imp3_comment = form.cleaned_data.get('imp3_comment')
                importance4 = form.cleaned_data.get('importance4')
                imp4_comment = form.cleaned_data.get('imp4_comment')
                importance5 = form.cleaned_data.get('importance5')
                importance6 = form.cleaned_data.get('importance6')
                importance7 = form.cleaned_data.get('importance7')
                imp7_comment = form.cleaned_data.get('imp7_comment')
                importance_test = True
                rcc_list = ['1.3.1.', '1.3.2.', '2.2.1.', '3.1.1.', '3.1.2.', '3.1.5.', '3.1.6.', '3.2.1.',
                            '3.2.3.', '3.3.1.', '4.1.1.', '4.1.2.', '4.2.1.', '4.2.2.', '4.3.1.', '4.4.1.',
                            '4.5.1.', '4.5.2.', '4.6.1.', '5.3.1.', '5.3.2.']
                if importance3 and (imp3_comment is None or imp3_comment == ""):
                    importance_test = False
                    form.add_error('imp3_comment', 'Пожалуйста, внесите данные')
                if importance4 and (imp4_comment is None or imp4_comment == ""):
                    importance_test = False
                    form.add_error('imp4_comment', 'Пожалуйста, внесите данные')
                if importance7 and (imp7_comment is None or imp7_comment == ""):
                    importance_test = False
                    form.add_error('imp7_comment', 'Пожалуйста, внесите данные')
                sum = 0
                for upload in form.files.getlist("cause_add_files"):
                    sum += upload.size
                print(root_cause_list)
                if (answer_date and answer_deadline and labor_costs_plan and comment and total_importance and
                        (root_cause_list is None or root_cause_list == "" or root_cause_list and
                        ("0." not in root_cause_list or ("0." in root_cause_list and root_cause_text != "")) and
                        (all(x not in root_cause_list for x in rcc_list) or (
                                any(x in root_cause_list for x in rcc_list) and root_cause_comment != ""))) and importance_test and sum <= MAX_FILE_UPLOAD):
                    try:
                        db_form.answer_date_plan = answer_date
                        db_form.answer_deadline_correct_plan = answer_deadline
                        db_form.labor_costs_plan = labor_costs_plan
                        db_form.comment = comment
                        db_form.answer_remark = answer_remark
                        db_form.total_importance = total_importance
                        db_form.root_cause_list = root_cause_list
                        db_form.root_cause_text = root_cause_text
                        db_form.root_cause_comment = root_cause_comment
                        db_form.importance1 = importance1
                        db_form.importance2 = importance2
                        db_form.importance3 = importance3
                        db_form.importance4 = importance4
                        db_form.importance5 = importance5
                        db_form.importance6 = importance6
                        db_form.importance7 = importance7
                        db_form.imp3_comment = imp3_comment
                        db_form.imp4_comment = imp4_comment
                        db_form.imp7_comment = imp7_comment
                        if importance1:
                            db_form.importance2 = None
                            db_form.importance3 = None
                            db_form.importance5 = None
                            db_form.importance6 = None
                            db_form.imp3_comment = None
                        if importance1 is False and importance2 is False:
                            db_form.importance3 = None
                            db_form.importance4 = None
                            db_form.importance5 = None
                            db_form.importance6 = None
                            db_form.importance7 = None
                            db_form.imp3_comment = None
                            db_form.imp4_comment = None
                            db_form.imp7_comment = None
                        if importance5 is False:
                            db_form.importance6 = None
                        if db_form.responsibleTrouble_name == db_form.gip or db_form.gip == request.user or db_form.gip in subs:
                            db_form.status = "На согласовании ГИПом"
                        else:
                            db_form.status = "На согласовании руководителем"
                        db_form.deadline = workDays(date.today(), 1)
                        db_form.save(update_fields=['answer_date_plan', 'answer_deadline_correct_plan',
                                                    'labor_costs_plan', 'comment', 'answer_remark', 'total_importance',
                                                    'root_cause_list',
                                                    'root_cause_comment', 'root_cause_text', 'status', 'deadline',
                                                    'importance1', 'importance2', 'importance3',
                                                    'importance4', 'importance5', 'importance6',
                                                    'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment'])
                        form.save_files(reestr=reest,
                                        name=form.cleaned_data.get('cause_file_name'),
                                        comment=form.cleaned_data.get('cause_file_comment'),
                                        remark=db_form.num_remark)
                        reest = reestInfo.objects.get(id=db_form.reestrID.id)
                        remarks = reestr.objects.filter((Q(reestrID=reest) & Q(actuality=True)))
                        step = True
                        for r in remarks:
                            if "согласовании" not in r.status:
                                step = False
                                break
                        if step:
                            if reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                                reest.status = "На согласовании"
                                reest.save(update_fields=['status'])
                            message = reest.project_dogovor.number[4:9] + reest.num_reestr
                            mails = []
                            mails.append(reest.gip.email)
                            for r in remarks:
                                mail = r.responsibleTrouble_name.email
                                if mail not in mails:
                                    mails.append(mail)
                            email_sender(mails, message, reest.id)
                        messages.success(request, "Изменения сохранены")
                    except Exception:
                        messages.error(request, "Возникла ошибка")
                if sum > MAX_FILE_UPLOAD:
                    messages.error(request,
                                   'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                       sum))
                if answer_date is None:
                    form.add_error('answer_date_plan', 'Пожалуйста, внесите данные')
                if answer_deadline is None:
                    form.add_error('answer_deadline_correct_plan', 'Пожалуйста, внесите данные')
                if labor_costs_plan is None:
                    form.add_error('labor_costs_plan', 'Пожалуйста, внесите данные')
                if form.cleaned_data.get('comment') == "":
                    form.add_error('comment', 'Пожалуйста, внесите данные')
                if total_importance == "":
                    form.add_error('total_importance', 'Пожалуйста, внесите данные')
                if "0." in root_cause_list and root_cause_text == "":
                    form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                    form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
            else:
                labor_costs_plan = form.cleaned_data.get('labor_costs_plan')
                comment = form.cleaned_data.get('comment')
                total_importance = form.cleaned_data.get('total_importance')
                root_cause_list = form.cleaned_data.get('root_cause_list')
                root_cause_text = form.cleaned_data.get('root_cause_text')
                answer_date = form.cleaned_data.get('answer_date_plan')
                answer_deadline = form.cleaned_data.get('answer_deadline_correct_plan')
                root_cause_comment = form.cleaned_data.get('root_cause_comment')
                rcc_list = ['1.3.1.', '1.3.2.', '2.2.1.', '3.1.1.', '3.1.2.', '3.1.5.', '3.1.6.', '3.2.1.',
                            '3.2.3.', '3.3.1.', '4.1.1.', '4.1.2.', '4.2.1.', '4.2.2.', '4.3.1.', '4.4.1.',
                            '4.5.1.', '4.5.2.', '4.6.1.', '5.3.1.', '5.3.2.']
                if answer_date is None:
                    form.add_error('answer_date_plan', 'Пожалуйста, внесите данные')
                if answer_deadline is None:
                    form.add_error('answer_deadline_correct_plan', 'Пожалуйста, внесите данные')
                if labor_costs_plan is None:
                    form.add_error('labor_costs_plan', 'Пожалуйста, внесите данные')
                if comment == "" or comment is None:
                    form.add_error('comment', 'Пожалуйста, внесите данные')
                if total_importance == "":
                    form.add_error('total_importance', 'Пожалуйста, внесите данные')
                if "0." in root_cause_list and root_cause_text == "":
                    form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                    form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
        else:
            form = emplForm(reest=db_form)
        if db_form.executor_fail_name is not None:
            exFName = db_form.executor_fail_name.last_name + ' ' + db_form.executor_fail_name.first_name
        else:
            exFName = ""
        if request.user == db_form.responsibleTrouble_name or db_form.responsibleTrouble_name in subs:
            next_step_key = True
        else:
            next_step_key = False
        return render(request, 'employee.html', {'form': form,
                                                 'gipcontext':
                                                     db_form.gip.last_name + ' ' +
                                                     db_form.gip.first_name,
                                                 'rescontext':
                                                     db_form.responsibleTrouble_name.last_name + ' ' +
                                                     db_form.responsibleTrouble_name.first_name,
                                                 'exfcontext': exFName,
                                                 'excontext':
                                                     db_form.executor_name.last_name + ' ' +
                                                     db_form.executor_name.first_name,
                                                 'customer': db_form.customer.name,
                                                 'contract_number': db_form.project_dogovor.number,
                                                 'reviewer': db_form.project_reviewer.name,
                                                 'reestrID': db_form.reestrID.id,
                                                 'remarkID': id,
                                                 'start_date': str(reest.start_date.year) + (
                                                     '-' if reest.start_date.month > 9 else '-0') + str(
                                                     reest.start_date.month) + (
                                                                   '-' if reest.start_date.day > 9 else '-0') + str(
                                                     reest.start_date.day),
                                                 'end_date': str(endDate.year) + (
                                                     '-' if endDate.month > 9 else '-0') + str(
                                                     endDate.month) + ('-' if endDate.day > 9 else '-0') + str(
                                                     endDate.day),
                                                 'emptyUserID': emptyUserID,
                                                 'next_step_key': next_step_key,
                                                 'comment_buf': db_form.comment
                                                 })
    else:
        return render(request, 'log_error.html',
                      {'text': "Пожалуйста, авторизируйтесь в качестве исполнителя, чтобы увидеть эту страницу."})


def boss2(request, id):
    if request.user.groups.filter(name='Руководитель').exists() or request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(name='Исполнитель').exists():
        db_form = reestr.objects.get(id=id)
        reest = reestInfo.objects.get(id=db_form.reestrID.id)
        endDate = reest.end_date - timedelta(days=1)
        if request.method == 'POST':
            form = BossForm2(db_form, request.POST, request.FILES or None)
            if form.is_valid():
                root_cause_list = form.cleaned_data.get('root_cause_list')
                root_cause_text = form.cleaned_data.get('root_cause_text')
                root_cause_comment = form.cleaned_data.get('root_cause-comment')
                executor_fail_name = form.cleaned_data.get('executor_fail_name')
                executor_fail_text = form.cleaned_data.get('executor_fail_text')
                importance1 = form.cleaned_data.get('importance1')
                importance2 = form.cleaned_data.get('importance2')
                importance3 = form.cleaned_data.get('importance3')
                imp3_comment = form.cleaned_data.get('imp3_comment')
                importance4 = form.cleaned_data.get('importance4')
                imp4_comment = form.cleaned_data.get('imp4_comment')
                importance5 = form.cleaned_data.get('importance5')
                importance6 = form.cleaned_data.get('importance6')
                importance7 = form.cleaned_data.get('importance7')
                imp7_comment = form.cleaned_data.get('imp7_comment')
                importance_test = True
                rcc_list = ['1.3.1.', '1.3.2.', '2.2.1.', '3.1.1.', '3.1.2.', '3.1.5.', '3.1.6.', '3.2.1.',
                            '3.2.3.', '3.3.1.', '4.1.1.', '4.1.2.', '4.2.1.', '4.2.2.', '4.3.1.', '4.4.1.',
                            '4.5.1.', '4.5.2.', '4.6.1.', '5.3.1.', '5.3.2.']
                if importance3 and (imp3_comment is None or imp3_comment == ""):
                    importance_test = False
                    form.add_error('imp3_comment', 'Пожалуйста, внесите данные')
                if importance4 and (imp4_comment is None or imp4_comment == ""):
                    importance_test = False
                    form.add_error('imp4_comment', 'Пожалуйста, внесите данные')
                if importance7 and (imp7_comment is None or imp7_comment == ""):
                    importance_test = False
                    form.add_error('imp7_comment', 'Пожалуйста, внесите данные')
                sum = 0
                for upload in form.files.getlist("cause_add_files"):
                    sum += upload.size
                if (((
                             executor_fail_name is not None and executor_fail_name.id == emptyUserID and executor_fail_text != "") or executor_fail_name is None or (
                             executor_fail_name.id != emptyUserID)) and (
                        "0." not in root_cause_list or ("0." in root_cause_list and root_cause_text != "")) and
                        (all(x not in root_cause_list for x in rcc_list) or (
                                any(x in root_cause_list for x in rcc_list) and root_cause_comment != "")) and importance_test and sum <= MAX_FILE_UPLOAD):
                    form.save(commit=False)
                    old_status = db_form.status
                    new_status = form.cleaned_data.get('status')
                    if importance1:
                        importance2 = None
                        importance3 = None
                        importance5 = None
                        importance6 = None
                        imp3_comment = None
                    if importance1 is False and importance2 is False:
                        importance3 = None
                        importance4 = None
                        importance5 = None
                        importance6 = None
                        importance7 = None
                        imp3_comment = None
                        imp4_comment = None
                        imp7_comment = None
                    if importance5 is False:
                        importance6 = None
                    try:
                        db_form.executor_fail_name = form.cleaned_data.get('executor_fail_name')
                        db_form.executor_fail_text = form.cleaned_data.get('executor_fail_text')
                        db_form.executor_name = form.cleaned_data.get('executor_name')
                        db_form.labor_costs_plan = form.cleaned_data.get('labor_costs_plan')
                        db_form.answer_remark = form.cleaned_data.get('answer_remark')
                        db_form.total_importance = form.cleaned_data.get('total_importance')
                        db_form.root_cause_list = form.cleaned_data.get('root_cause_list')
                        db_form.root_cause_text = form.cleaned_data.get('root_cause_text')
                        db_form.root_cause_comment = form.cleaned_data.get(
                            'root_cause_comment') if form.cleaned_data.get('root_cause_comment') is not None else ''
                        db_form.answer_date_plan = form.cleaned_data.get('answer_date_plan')
                        db_form.answer_deadline_correct_plan = form.cleaned_data.get('answer_deadline_correct_plan')
                        db_form.importance1 = importance1
                        db_form.importance2 = importance2
                        db_form.importance3 = importance3
                        db_form.importance4 = importance4
                        db_form.importance5 = importance5
                        db_form.importance6 = importance6
                        db_form.importance7 = importance7
                        db_form.imp3_comment = imp3_comment
                        db_form.imp4_comment = imp4_comment
                        db_form.imp7_comment = imp7_comment
                        if db_form.comment != form.cleaned_data.get('comment') and form.cleaned_data.get(
                                'comment') != "":
                            d = datetime.now()
                            db_form.comment = (form.cleaned_data.get("comment") + " (" + str(d.hour) + ':' + str(
                                d.minute) + ':' +
                                               str(d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(
                                        d.year) + ' ' +
                                               shortName(request.user) + ")")
                        if old_status != new_status:
                            try:
                                next = True
                                remarks = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(actuality=True)))
                                reest = reestInfo.objects.get(id=db_form.reestrID.id)
                                if new_status == "На согласовании ГИПом":
                                    db_form.status = new_status
                                    db_form.save()
                                    form.save_files(reestr=reest,
                                                    name=form.cleaned_data.get('cause_file_name'),
                                                    comment=form.cleaned_data.get('cause_file_comment'),
                                                    remark=db_form.num_remark)
                                    messages.success(request, "Замечание согласовано")
                                elif new_status == "На доработке":
                                    if db_form.comment != form.cleaned_data.get('comment') and form.cleaned_data.get(
                                            'comment') != "":
                                        if db_form.executor_name == db_form.responsibleTrouble_name:
                                            db_form.status = "На доработке руководителем"
                                            db_form.save()

                                        else:
                                            db_form.status = "На доработке исполнителем"
                                            db_form.save()
                                        form.save_files(reestr=reest,
                                                        name=form.cleaned_data.get('cause_file_name'),
                                                        comment=form.cleaned_data.get('cause_file_comment'),
                                                        remark=db_form.num_remark)
                                        mails = []
                                        for r in remarks:
                                            if "доработке" not in r.status:
                                                next = False
                                                break
                                            elif r.status == "На доработке руководителем":
                                                mails.append(r.responsibleTrouble_name.email)
                                            elif r.status == "На доработке исполнителем":
                                                mails.append(r.executor_name.email)
                                        if next:
                                            message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                            email_sender(np.unique(np.array(mails)), message, reest.id)
                                        messages.error(request, "Замечание отклонено")
                                    else:
                                        messages.error(request, "Внесите причину отклонения в п. 10.3 Комментарии")
                            except Exception as e:
                                messages.error(request, "Возникла ошибка")
                        else:
                            db_form.save()
                            form.save_files(reestr=reest,
                                            name=form.cleaned_data.get('cause_file_name'),
                                            comment=form.cleaned_data.get('cause_file_comment'),
                                            remark=db_form.num_remark)
                        messages.success(request, "Изменения сохранены")
                        return render(request, 'boss2.html', {'form': form,
                                                              'gipcontext':
                                                                  db_form.gip.last_name + ' ' +
                                                                  db_form.gip.first_name,
                                                              'rescontext':
                                                                  db_form.responsibleTrouble_name.last_name + ' ' +
                                                                  db_form.responsibleTrouble_name.first_name,
                                                              'reestrID': db_form.reestrID.id,
                                                              'customer': db_form.customer.name,
                                                              'contract_number': db_form.project_dogovor.number,
                                                              'reviewer': db_form.project_reviewer.name,
                                                              'emptyUserID': emptyUserID,
                                                              'start_date': str(reest.start_date.year) + (
                                                                  '-' if reest.start_date.month > 9 else '-0') + str(
                                                                  reest.start_date.month) + (
                                                                                '-' if reest.start_date.day > 9 else '-0') + str(
                                                                  reest.start_date.day),
                                                              'end_date': str(endDate.year) + (
                                                                  '-' if endDate.month > 9 else '-0') + str(
                                                                  endDate.month) +
                                                                          ('-' if endDate.day > 9 else '-0') + str(
                                                                  endDate.day),
                                                              })
                    except Exception:
                        messages.error(request, "Возникла ошибка")
                else:
                    if sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    if "0." in root_cause_list and root_cause_text == "":
                        form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                    if executor_fail_name and executor_fail_name.id == emptyUserID and executor_fail_text == "":
                        form.add_error('executor_fail_text', 'Пожалуйста, внесите данные')
                    if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                        form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
            else:
                return render(request, 'boss2.html', {'form': form,
                                                      'gipcontext':
                                                          db_form.gip.last_name + ' ' +
                                                          db_form.gip.first_name,
                                                      'rescontext':
                                                          db_form.responsibleTrouble_name.last_name + ' ' +
                                                          db_form.responsibleTrouble_name.first_name,
                                                      'reestrID': db_form.reestrID.id,
                                                      'customer': db_form.customer.name,
                                                      'contract_number': db_form.project_dogovor.number,
                                                      'reviewer': db_form.project_reviewer.name,
                                                      'emptyUserID': emptyUserID,
                                                      'start_date': str(reest.start_date.year) + (
                                                          '-' if reest.start_date.month > 9 else '-0') + str(
                                                          reest.start_date.month) + (
                                                                        '-' if reest.start_date.day > 9 else '-0') + str(
                                                          reest.start_date.day),
                                                      'end_date': str(endDate.year) + (
                                                          '-' if endDate.month > 9 else '-0') + str(
                                                          endDate.month) + ('-' if endDate.day > 9 else '-0') + str(
                                                          endDate.day),
                                                      })
        else:
            form = BossForm2(reestr.objects.get(id=id))
        return render(request, 'boss2.html', {'form': form,
                                              'gipcontext':
                                                  db_form.gip.last_name + ' ' +
                                                  db_form.gip.first_name,
                                              'rescontext':
                                                  db_form.responsibleTrouble_name.last_name + ' ' +
                                                  db_form.responsibleTrouble_name.first_name,
                                              'reestrID': db_form.reestrID.id,
                                              'customer': db_form.customer.name,
                                              'contract_number': db_form.project_dogovor.number,
                                              'reviewer': db_form.project_reviewer.name,
                                              'emptyUserID': emptyUserID,
                                              'start_date': str(reest.start_date.year) + (
                                                  '-' if reest.start_date.month > 9 else '-0') + str(
                                                  reest.start_date.month) + (
                                                                '-' if reest.start_date.day > 9 else '-0') + str(
                                                  reest.start_date.day),
                                              'end_date': str(endDate.year) + (
                                                  '-' if endDate.month > 9 else '-0') + str(
                                                  endDate.month) + ('-' if endDate.day > 9 else '-0') + str(
                                                  endDate.day),
                                              })
    else:
        return render(request, 'log_error.html',
                      {'text': "Пожалуйста, авторизируйтесь в качестве руководителя, чтобы увидеть эту страницу."})


def gip2(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.is_superuser:
        db_form = reestr.objects.get(id=id)
        reest = reestInfo.objects.get(id=db_form.reestrID.id)
        endDate = reest.end_date - timedelta(days=1)
        if request.method == 'POST':
            form = GIPform2(reestr.objects.get(id=id), request.POST, request.FILES or None)
            if form.is_valid():
                root_cause_list = form.cleaned_data.get('root_cause_list')
                root_cause_text = form.cleaned_data.get('root_cause_text')
                root_cause_comment = form.cleaned_data.get('root_cause_comment')
                importance1 = form.cleaned_data.get('importance1')
                importance2 = form.cleaned_data.get('importance2')
                importance3 = form.cleaned_data.get('importance3')
                imp3_comment = form.cleaned_data.get('imp3_comment')
                importance4 = form.cleaned_data.get('importance4')
                imp4_comment = form.cleaned_data.get('imp4_comment')
                importance5 = form.cleaned_data.get('importance5')
                importance6 = form.cleaned_data.get('importance6')
                importance7 = form.cleaned_data.get('importance7')
                imp7_comment = form.cleaned_data.get('imp7_comment')
                importance_test = True
                rcc_list = ['1.3.1.', '1.3.2.', '2.2.1.', '3.1.1.', '3.1.2.', '3.1.5.', '3.1.6.', '3.2.1.',
                            '3.2.3.', '3.3.1.', '4.1.1.', '4.1.2.', '4.2.1.', '4.2.2.', '4.3.1.', '4.4.1.',
                            '4.5.1.', '4.5.2.', '4.6.1.', '5.3.1.', '5.3.2.']
                executor_fail_name = form.cleaned_data.get('executor_fail_name')
                executor_fail_text = form.cleaned_data.get('executor_fail_text')
                sum = 0
                for upload in form.files.getlist('cause_add_files'):
                    sum += upload.size
                if importance3 and (imp3_comment is None or imp3_comment == ""):
                    importance_test = False
                    form.add_error('imp3_comment', 'Пожалуйста, внесите данные')
                if importance4 and (imp4_comment is None or imp4_comment == ""):
                    importance_test = False
                    form.add_error('imp4_comment', 'Пожалуйста, внесите данные')
                if importance7 and (imp7_comment is None or imp7_comment == ""):
                    importance_test = False
                    form.add_error('imp7_comment', 'Пожалуйста, внесите данные')
                if (((
                             executor_fail_name is not None and executor_fail_name.id == emptyUserID and executor_fail_text != "") or executor_fail_name is None or (
                             executor_fail_name.id != emptyUserID)) and (
                        "0." not in root_cause_list or ("0." in root_cause_list and root_cause_text != "")) and
                        (all(x not in root_cause_list for x in rcc_list) or (
                                any(x in root_cause_list for x in rcc_list) and root_cause_comment != ""))
                        and importance_test and sum <= MAX_FILE_UPLOAD):
                    form.save(commit=False)
                    old_status = db_form.status
                    new_status = form.cleaned_data.get('status')
                    if old_status == "На заполнении ГИПом" and reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                        reest.status = "На заполнении"
                        reest.save(update_fields=['status'])
                        if db_form.responsibleTrouble_name.id != request.user.id:
                            new_status = "На заполнении руководителем"
                        elif db_form.executor_name.id != request.user.id:
                            new_status = "На заполнении исполнителем"
                        else:
                            new_status = "На согласовании ГИПом"
                    if importance1:
                        importance2 = None
                        importance3 = None
                        importance5 = None
                        importance6 = None
                        imp3_comment = None
                    if importance1 is False and importance2 is False:
                        importance3 = None
                        importance4 = None
                        importance5 = None
                        importance6 = None
                        importance7 = None
                        imp3_comment = None
                        imp4_comment = None
                        imp7_comment = None
                    if importance5 is False:
                        importance6 = None
                    try:
                        db_form.remark_name = form.cleaned_data.get('remark_name')
                        db_form.rational = form.cleaned_data.get('rational')
                        db_form.designation_name = form.cleaned_data.get('designation_name')
                        db_form.section_name = form.cleaned_data.get('section_name')
                        db_form.executor_fail_name = form.cleaned_data.get('executor_fail_name')
                        db_form.executor_fail_text = form.cleaned_data.get('executor_fail_text')
                        db_form.executor_name = form.cleaned_data.get('executor_name')
                        db_form.labor_costs_plan = form.cleaned_data.get('labor_costs_plan')
                        db_form.answer_remark = form.cleaned_data.get('answer_remark')
                        db_form.total_importance = form.cleaned_data.get('total_importance')
                        db_form.root_cause_list = form.cleaned_data.get('root_cause_list')
                        db_form.root_cause_text = form.cleaned_data.get('root_cause_text')
                        db_form.root_cause_comment = form.cleaned_data.get(
                            'root_cause_comment') if form.cleaned_data.get('root_cause_comment') is not None else ''
                        db_form.answer_date_plan = form.cleaned_data.get('answer_date_plan')
                        db_form.answer_deadline_correct_plan = form.cleaned_data.get('answer_deadline_correct_plan')
                        db_form.importance1 = importance1
                        db_form.importance2 = importance2
                        db_form.importance3 = importance3
                        db_form.importance4 = importance4
                        db_form.importance5 = importance5
                        db_form.importance6 = importance6
                        db_form.importance7 = importance7
                        db_form.imp3_comment = imp3_comment
                        db_form.imp4_comment = imp4_comment
                        db_form.imp7_comment = imp7_comment
                        if db_form.comment != form.cleaned_data.get('comment') and form.cleaned_data.get(
                                'comment') != "":
                            d = datetime.now()
                            db_form.comment = (form.cleaned_data.get("comment") + " (" + str(d.hour) + ':' + str(
                                d.minute) + ':' +
                                               str(d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(
                                        d.year) + ' ' +
                                               shortName(request.user) + ")")
                        if db_form.responsibleTrouble_name != form.cleaned_data.get(
                                'responsibleTrouble_name') and form.cleaned_data.get('responsibleTrouble_name') != "":
                            db_form.responsibleTrouble_name = form.cleaned_data.get('responsibleTrouble_name')
                            db_form.department = departments.objects.get(
                                user=form.cleaned_data.get('responsibleTrouble_name')).department
                        if old_status != new_status:
                            try:
                                next = True
                                remarks = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(actuality=True)))
                                if new_status == "Согласовано ГИПом":
                                    dep_remarks = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(
                                        actuality=True) & Q(responsibleTrouble_name=db_form.responsibleTrouble_name)))
                                    dep_remarks_approved = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(
                                        actuality=True) & Q(
                                        responsibleTrouble_name=db_form.responsibleTrouble_name) & Q(
                                        status="Согласовано ГИПом")))
                                    if reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                                        print(len(dep_remarks) - len(dep_remarks_approved))
                                        if len(dep_remarks) - len(dep_remarks_approved) <= 1:
                                            message_to = []
                                            for r in dep_remarks:
                                                message_to.append(r.executor_name.email)
                                                if r.executor_name == r.gip:
                                                    r.status = "Подготовка ответов ГИПом"
                                                    r.save()
                                                elif r.responsibleTrouble_name == r.executor_name:
                                                    r.status = "Подготовка ответов руководителем"
                                                    r.save()
                                                else:
                                                    r.status = "Подготовка ответов исполнителем"
                                                    r.save()
                                            message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                            email_sender(np.unique(np.array(message_to)), message, reest.id)
                                        else:
                                            db_form.status = new_status
                                            db_form.save()
                                    else:
                                        if db_form.responsibleTrouble_name == request.user.id and db_form.executor_name.id == request.user.id:
                                            db_form.status = "Подготовка ответов ГИПом"
                                            db_form.save()
                                        elif db_form.responsibleTrouble_name == db_form.executor_name:
                                            db_form.status = "Подготовка ответов руководителем"
                                            db_form.save()
                                        else:
                                            db_form.status = "Подготовка ответов исполнителем"
                                            db_form.save()
                                    for r in remarks:
                                        if r.status not in ["Согласовано ГИПом", "Принято ГИПом"] and 'Подготовка' not in r.status:
                                            next = False
                                            break
                                    if next and reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                                        reest.status = "Согласовано ГИПом"
                                        reest.save(update_fields=['status'])
                                    messages.success(request, "Замечание согласовано")
                                elif new_status == "На доработке":
                                    if db_form.comment != form.cleaned_data.get('comment') and form.cleaned_data.get(
                                            'comment') != "":
                                        if db_form.responsibleTrouble_name == request.user.id and db_form.executor_name.id == request.user.id:
                                            db_form.status = "На доработке ГИПом"
                                            db_form.save()
                                        elif db_form.responsibleTrouble_name == db_form.executor_name:
                                            db_form.status = "На доработке руководителем"
                                            db_form.save()
                                        else:
                                            db_form.status = "На доработке исполнителем"
                                            db_form.save()
                                        remarks = reestr.objects.filter((Q(reestrID=reest) & Q(actuality=True)))
                                        send = True
                                        mails = []
                                        for r in remarks:
                                            if "доработке" not in r.status:
                                                send = False
                                                break
                                            elif r.status == "На доработке исполнителем":
                                                mails.append(r.executor_name.email)
                                            elif r.status == "На доработке руководителем":
                                                mails.append(r.responsibleTrouble_name.email)
                                        if send:
                                            message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                            email_sender(np.unique(np.array(mails)), message, reest.id)
                                        messages.error(request, "Замечание отклонено")
                                    else:
                                        messages.error(request, "Внесите причину отклонения в п. 10.3 Комментарии")
                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                messages.error(request, "Возникла ошибка " + str(e) + " " + str(exc_tb.tb_lineno))
                        else:
                            try:
                                db_form.save()
                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                messages.error(request, "Возникла ошибка " + str(e) + " " + str(exc_tb.tb_lineno))
                        name = form.cleaned_data.get("file_name")
                        file_comment = form.cleaned_data.get("file_comment")
                        cause_comment = form.cleaned_data.get("cause_file_comment")
                        cause_name = form.cleaned_data.get("cause_file_name")
                        form.save_files(reestInfo.objects.get(id=db_form.reestrID.id), name, file_comment, cause_name,
                                        cause_comment, form.cleaned_data.get("num_remark"))
                        messages.success(request, "Изменения сохранены")
                        return render(request, 'GIP2.html', {'form': form,
                                                             'gipcontext':
                                                                 db_form.gip.last_name + ' ' +
                                                                 db_form.gip.first_name,
                                                             'rescontext':
                                                                 db_form.responsibleTrouble_name.last_name + ' ' +
                                                                 db_form.responsibleTrouble_name.first_name,
                                                             'reestrID': reest.id,
                                                             'emptyUserID': emptyUserID,
                                                             })
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        messages.error(request, "Возникла ошибка " + str(e) + " " + str(exc_tb.tb_lineno))
                else:
                    if sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    if "0." in root_cause_list and root_cause_text == "":
                        form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                    if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                        form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
                    if executor_fail_name is not None and executor_fail_name.id == emptyUserID and executor_fail_text == "":
                        form.add_error('executor_fail_text', 'Пожалуйста, внесите данные')
            else:
                return render(request, 'GIP2.html', {'form': form,
                                                     'gipcontext':
                                                         db_form.gip.last_name + ' ' +
                                                         db_form.gip.first_name,
                                                     'rescontext':
                                                         db_form.responsibleTrouble_name.last_name + ' ' +
                                                         db_form.responsibleTrouble_name.first_name,
                                                     'reestrID': reest.id,
                                                     'customer': db_form.customer.name,
                                                     'contract_number': db_form.project_dogovor.number,
                                                     'reviewer': db_form.project_reviewer.name,
                                                     'emptyUserID': emptyUserID,
                                                     'start_date': str(reest.start_date.year) + (
                                                         '-' if reest.start_date.month > 9 else '-0') + str(
                                                         reest.start_date.month) + (
                                                                       '-' if reest.start_date.day > 9 else '-0') + str(
                                                         reest.start_date.day),
                                                     'end_date': str(endDate.year) + (
                                                         '-' if endDate.month > 9 else '-0') + str(
                                                         endDate.month) + ('-' if endDate.day > 9 else '-0') + str(
                                                         endDate.day),
                                                     })
        else:
            form = GIPform2(reestr.objects.get(id=id))
        return render(request, 'GIP2.html', {'form': form,
                                             'gipcontext':
                                                 db_form.gip.last_name + ' ' +
                                                 db_form.gip.first_name,
                                             'rescontext':
                                                 db_form.responsibleTrouble_name.last_name + ' ' +
                                                 db_form.responsibleTrouble_name.first_name,
                                             'reestrID': reest.id,
                                             'customer': db_form.customer.name,
                                             'contract_number': db_form.project_dogovor.number,
                                             'reviewer': db_form.project_reviewer.name,
                                             'emptyUserID': emptyUserID,
                                             'start_date': str(reest.start_date.year) + (
                                                 '-' if reest.start_date.month > 9 else '-0') + str(
                                                 reest.start_date.month) + (
                                                               '-' if reest.start_date.day > 9 else '-0') + str(
                                                 reest.start_date.day),
                                             'end_date': str(endDate.year) + (
                                                 '-' if endDate.month > 9 else '-0') + str(
                                                 endDate.month) + ('-' if endDate.day > 9 else '-0') + str(
                                                 endDate.day),
                                             })
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или администратора, чтобы увидеть эту страницу."})

def answer(request, id):
    if request.user.groups.filter(name='Руководитель').exists() or request.user.groups.filter(name='Исполнитель').exists() or request.user.groups.filter(
            name='ГИП').exists() or request.user.is_superuser:
        if request.user.groups.filter(name='Руководитель').exists() or request.user.groups.filter(name='Исполнитель').exists():
            group = "Руководитель"
        else:
            group = "ГИП"
        db_form = reestr.objects.get(id=id)
        rcc_list = ['1.3.1.', '1.3.2.', '2.2.1.', '3.1.1.', '3.1.2.', '3.1.5.', '3.1.6.', '3.2.1.',
                    '3.2.3.', '3.3.1.', '4.1.1.', '4.1.2.', '4.2.1.', '4.2.2.', '4.3.1.', '4.4.1.',
                    '4.5.1.', '4.5.2.', '4.6.1.', '5.3.1.', '5.3.2.']
        if request.method == 'POST':
            form = AnswerForm(db_form, request.POST or None)
            if form.is_valid():
                old_status = db_form.status
                new_status = form.cleaned_data.get('status')
                db_form.answer_date_fact = form.cleaned_data.get('answer_date_fact')
                db_form.answer_deadline_correct_fact = form.cleaned_data.get('answer_deadline_correct_fact')
                db_form.labor_costs_fact = form.cleaned_data.get('labor_costs_fact')
                db_form.answer_remark = form.cleaned_data.get('answer_remark')
                db_form.link_tech_name = form.cleaned_data.get('link_tech_name')
                if db_form.comment != form.cleaned_data.get('comment') and form.cleaned_data.get('comment') != "":
                    d = datetime.now()
                    db_form.comment = form.cleaned_data.get('comment') + " (" + str(d.hour) + ':' + str(
                        d.minute) + ':' + str(
                        d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(d.year) + ' ' + shortName(
                        request.user) + ")"
                root_cause_list = form.cleaned_data.get('root_cause_list')
                root_cause_text = form.cleaned_data.get('root_cause_text')
                root_cause_comment = form.cleaned_data.get('root_cause_comment')
                db_form.root_cause_list = form.cleaned_data.get('root_cause_list')
                db_form.root_cause_text = form.cleaned_data.get('root_cause_text')
                db_form.root_cause_comment = form.cleaned_data.get('root_cause_comment')
                name = form.cleaned_data.get("cause_file_name")
                file_comment = form.cleaned_data.get("cause_file_comment")
                remark = form.cleaned_data.get("num_remark")
                try:
                    sum2 = 0
                    for upload in form.files.getlist("cause_add_files"):
                        sum2 += upload.size
                    if root_cause_list and ("0." not in root_cause_list or ("0." in root_cause_list and root_cause_text != "")) and ((all(x not in root_cause_list for x in rcc_list) or (
                                    any(x in root_cause_list for x in rcc_list) and root_cause_comment != "")) and
                             sum2 <= MAX_FILE_UPLOAD):
                        try:
                            next = True
                            remarks = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(actuality=True)))
                            reest = reestInfo.objects.get(id=db_form.reestrID.id)
                            if new_status == "Принято ГИПом" and old_status != new_status:
                                db_form.status = new_status
                                db_form.save()
                                form.save_files(reest, name, file_comment, remark)
                                for r in remarks:
                                    if r.status != "Принято ГИПом":
                                        next = False
                                        break
                                if next and reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                                    reest.status = "Принято ГИПом"
                                    reest.save(update_fields=['status'])
                                messages.success(request, "Замечание согласовано")
                            elif (new_status == "На доработке руководителем" or new_status == "На доработке исполнителем") and old_status != new_status:
                                if db_form.comment != form.cleaned_data.get('comment') and form.cleaned_data.get(
                                        'comment') != "":
                                    db_form.status = new_status
                                    db_form.save()
                                    form.save_files(reest, name, file_comment, remark)
                                    mails = []
                                    for r in remarks:
                                        if "доработке" not in r.status:
                                            next = False
                                            break
                                        elif r.status == "На доработке руководителем":
                                            mails.append(db_form.responsibleTrouble_name.email)
                                        elif r.status == "На доработке исполнителем":
                                            mails.append(db_form.executor_name.email)
                                    if next:
                                        message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                        email_sender(np.unique(np.array(mails)), message, reest.id)
                                    messages.error(request, "Замечание отклонено")
                                else:
                                    messages.error(request, "Внесите причину отклонения в п. 10.3 Комментарии")
                            elif new_status == "На согласовании ГИПом" and old_status != new_status:
                                db_form.status = new_status
                                db_form.save()
                                form.save_files(reest, name, file_comment, remark)
                                mails = []
                                for r in remarks:
                                    if "согласовании" not in r.status:
                                        next = False
                                        break
                                    elif r.status == "На согласовании руководителем":
                                        mails.append(r.responsibleTrouble_name.email)
                                    elif r.status == "На согласовании ГИПом":
                                        mails.append(r.gip.email)
                                if next:
                                    if reest.status != "На согласовании" and reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                                        reest.status = "На согласовании"
                                        reest.save(update_fields=['status'])
                                    mails.append(db_form.gip.email)
                                    message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                    email_sender(np.unique(np.array(mails)), message, reest.id)
                                messages.success(request, "Замечание согласовано")
                            else:
                                db_form.save()
                                form.save_files(reest, name, file_comment, remark)
                        except Exception:
                            messages.error(request, "Возникла ошибка")
                        messages.success(request, "Изменения сохранены")
                        return render(request, 'answer.html', {'form': form,
                                                               'gipcontext':
                                                                   db_form.gip.last_name + ' ' +
                                                                   db_form.gip.first_name if db_form.gip else '',
                                                               'rescontext':
                                                                   db_form.responsibleTrouble_name.last_name + ' ' +
                                                                   db_form.responsibleTrouble_name.first_name if db_form.responsibleTrouble_name else '',
                                                               'exfcontext':
                                                                   db_form.executor_fail_name.last_name + ' ' +
                                                                   db_form.executor_fail_name.first_name if db_form.executor_fail_name else '',
                                                               'excontext':
                                                                   db_form.executor_name.last_name + ' ' +
                                                                   db_form.executor_name.first_name if db_form.executor_name else '',
                                                               'group': group,
                                                               'reestrID': db_form.reestrID.id})
                    if sum2 > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    if "0." in root_cause_list and root_cause_text == "":
                        form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                    if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                        form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
                except Exception:
                    messages.error(request, "Возникла ошибка")
            else:
                return render(request, 'answer.html', {'form': form,
                                                       'gipcontext':
                                                           db_form.gip.last_name + ' ' +
                                                           db_form.gip.first_name if db_form.gip else '',
                                                       'rescontext':
                                                           db_form.responsibleTrouble_name.last_name + ' ' +
                                                           db_form.responsibleTrouble_name.first_name if db_form.responsibleTrouble_name else '',
                                                       'exfcontext':
                                                           db_form.executor_fail_name.last_name + ' ' +
                                                           db_form.executor_fail_name.first_name if db_form.executor_fail_name else '',
                                                       'excontext':
                                                           db_form.executor_name.last_name + ' ' +
                                                           db_form.executor_name.first_name if db_form.executor_name else '',
                                                       'group': group,
                                                       'reestrID': db_form.reestrID.id})
        else:
            form = AnswerForm(reestr.objects.get(id=id))
        return render(request, 'answer.html', {'form': form,
                                               'gipcontext':
                                                   db_form.gip.last_name + ' ' +
                                                   db_form.gip.first_name if db_form.gip else '',
                                               'rescontext':
                                                   db_form.responsibleTrouble_name.last_name + ' ' +
                                                   db_form.responsibleTrouble_name.first_name if db_form.responsibleTrouble_name else '',
                                               'exfcontext':
                                                   db_form.executor_fail_name.last_name + ' ' +
                                                   db_form.executor_fail_name.first_name if db_form.executor_fail_name else '',
                                               'excontext':
                                                   db_form.executor_name.last_name + ' ' +
                                                   db_form.executor_name.first_name if db_form.executor_name else '',
                                               'group': group,
                                               'customer': db_form.customer.name,
                                               'contract_number': db_form.project_dogovor.number,
                                               'reviewer': db_form.project_reviewer.name,
                                               'reestrID': db_form.reestrID.id})
    else:
        return render(request, 'log_error.html', {
            'text': "Пожалуйста, авторизируйтесь в качестве ГИПа, руководителя или администратора, чтобы увидеть эту страницу."})


def final(request, id):
    if request.user.groups.filter(name='Руководитель').exists() or request.user.groups.filter(
            name='ГИП').exists() or request.user.groups.filter(name='Исполнитель').exists():
        db_form = reestr.objects.get(id=id)
        if request.user.groups.filter(name='Руководитель').exists():
            role = "Руководитель"
        elif request.user.groups.filter(name='Исполнитель').exists():
            role = "Исполнитель"
        else:
            role = "ГИП"
        try:
            subs = departments.objects.get(user=request.user.id).substitute.all()
        except Exception:
            subs = []
        rcc_list = ['1.3.1.', '1.3.2.', '2.2.1.', '3.1.1.', '3.1.2.', '3.1.5.', '3.1.6.', '3.2.1.',
                    '3.2.3.', '3.3.1.', '4.1.1.', '4.1.2.', '4.2.1.', '4.2.2.', '4.3.1.', '4.4.1.',
                    '4.5.1.', '4.5.2.', '4.6.1.', '5.3.1.', '5.3.2.']
        if request.method == 'POST':
            form = FinalForm(db_form, request.POST, request.FILES or None)
            if request.POST.get('receiving') == 'true':
                print("отправка")
                if form.is_valid():
                    print("форма заполнена")
                    labor_costs_fact = form.cleaned_data.get('labor_costs_fact')
                    answer_remark = form.cleaned_data.get('answer_remark')
                    link_tech_name = form.cleaned_data.get('link_tech_name')
                    answer_date = form.cleaned_data.get('answer_date_fact')
                    answer_deadline = form.cleaned_data.get('answer_deadline_correct_fact')
                    comment = form.cleaned_data.get('comment')
                    root_cause_list = form.cleaned_data.get('root_cause_list')
                    root_cause_text = form.cleaned_data.get('root_cause_text')
                    root_cause_comment = form.cleaned_data.get('root_cause_comment')
                    sum = 0
                    for upload in form.files.getlist("add_files"):
                        sum += upload.size
                    sum2 = 0
                    for upload in form.files.getlist("cause_add_files"):
                        sum2 += upload.size
                    if (answer_date and answer_deadline and labor_costs_fact and answer_remark != "" and link_tech_name != "" and root_cause_list and
                            ("0." not in root_cause_list or ("0." in root_cause_list and root_cause_text != "")) and
                            (all(x not in root_cause_list for x in rcc_list) or (
                                    any(x in root_cause_list for x in rcc_list) and root_cause_comment != "")) and
                             sum <= MAX_FILE_UPLOAD and sum2 <= MAX_FILE_UPLOAD):
                        try:
                            db_form.answer_date_fact = answer_date
                            db_form.answer_deadline_correct_fact = answer_deadline
                            db_form.labor_costs_fact = labor_costs_fact
                            db_form.answer_remark = answer_remark
                            db_form.link_tech_name = link_tech_name
                            db_form.root_cause_list = root_cause_list
                            db_form.root_cause_text = root_cause_text
                            db_form.root_cause_comment = root_cause_comment
                            if db_form.comment != comment and comment != "":
                                d = datetime.now()
                                db_form.comment = comment + " (" + str(d.hour) + ':' + str(d.minute) + ':' + str(
                                    d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(d.year) + ' ' + shortName(
                                    request.user) + ")"
                            if db_form.responsibleTrouble_name == db_form.gip or db_form.gip == request.user or db_form.gip in subs:
                                db_form.status = "На согласовании ГИПом"
                            else:
                                db_form.status = "На согласовании руководителем"
                            db_form.save(
                                update_fields=['labor_costs_fact', 'answer_remark', 'link_tech_name', 'answer_date_fact',
                                               'answer_deadline_correct_fact', 'status', 'comment', 'root_cause_list', 'root_cause_text', 'root_cause_comment'])
                            remarks = reestr.objects.filter((Q(reestrID=db_form.reestrID) & Q(actuality=True)))
                            step1 = True
                            for r in remarks:
                                if "согласовании" not in r.status:
                                    step1 = False
                                    break
                            if step1:
                                reest = reestInfo.objects.get(id=db_form.reestrID.id)
                                if reest.status != "На согласовании Рецензентом" and reest.status != "На доработке":
                                    reest.status = "На согласовании"
                                    reest.save(update_fields=['status'])
                                message = reest.project_dogovor.number[4:9] + reest.num_reestr
                                mails = []
                                for r in remarks:
                                    if r.status == "На согласовании ГИПом":
                                        mail = reest.gip.email
                                        if mail not in mails:
                                            mails.append(mail)
                                    else:
                                        mail = r.responsibleTrouble_name.email
                                        if mail not in mails:
                                            mails.append(mail)
                                email_sender(mails, message, reest.id)
                                messages.success(request, "Изменения сохранены")
                            name = form.cleaned_data.get("file_name")
                            file_comment = form.cleaned_data.get("file_comment")
                            remark = form.cleaned_data.get("num_remark")
                            form.save_files(reestInfo.objects.get(id=db_form.reestrID.id), name, file_comment, remark)
                            messages.success(request, "Изменения сохранены")
                        except Exception as e:
                            messages.error(request, "Возникла ошибка " + str(e))
                    if sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    if sum2 > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    if answer_date is None:
                        form.add_error('answer_date_fact', 'Пожалуйста, внесите данные')
                    if answer_deadline is None:
                        form.add_error('answer_deadline_correct_fact', 'Пожалуйста, внесите данные')
                    if labor_costs_fact is None:
                        form.add_error('labor_costs_fact', 'Пожалуйста, внесите данные')
                    if answer_remark == "":
                        form.add_error('answer_remark', 'Пожалуйста, внесите данные')
                    if link_tech_name == "":
                        form.add_error('link_tech_name', 'Пожалуйста, внесите данные')
                    if "0." in root_cause_list and root_cause_text == "":
                        form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                    if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                        form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
                else:
                    print("форма пустая")
                    labor_costs_fact = form.cleaned_data.get('labor_costs_fact')
                    answer_remark = form.cleaned_data.get('answer_remark')
                    link_tech_name = form.cleaned_data.get('link_tech_name')
                    answer_date = form.cleaned_data.get('answer_date_fact')
                    answer_deadline = form.cleaned_data.get('answer_deadline_correct_fact')
                    root_cause_list = form.cleaned_data.get('root_cause_list')
                    root_cause_text = form.cleaned_data.get('root_cause_text')
                    root_cause_comment = form.cleaned_data.get('root_cause_comment')
                    if answer_date is None:
                        form.add_error('answer_date_fact', 'Пожалуйста, внесите данные')
                    if answer_deadline is None:
                        form.add_error('answer_deadline_correct_fact', 'Пожалуйста, внесите данные')
                    if labor_costs_fact is None:
                        form.add_error('labor_costs_fact', 'Пожалуйста, внесите данные')
                    if answer_remark == "":
                        form.add_error('answer_remark', 'Пожалуйста, внесите данные')
                    if link_tech_name == "":
                        form.add_error('link_tech_name', 'Пожалуйста, внесите данные')
                    if root_cause_list:
                        if "0." in root_cause_list and root_cause_text == "":
                            form.add_error('root_cause_text', 'Пожалуйста, внесите данные')
                        if any(x in root_cause_list for x in rcc_list) and root_cause_comment == "":
                            form.add_error('root_cause_comment', 'Пожалуйста, внесите данные')
            else:
                print('сохранение')
                if form.is_valid():
                    print("форма заполнена")
                    try:
                        labor_costs_fact = form.cleaned_data.get('labor_costs_fact')
                        answer_remark = form.cleaned_data.get('answer_remark')
                        link_tech_name = form.cleaned_data.get('link_tech_name')
                        answer_date = form.cleaned_data.get('answer_date_fact')
                        answer_deadline = form.cleaned_data.get('answer_deadline_correct_fact')
                        comment = form.cleaned_data.get('comment')
                        root_cause_list = form.cleaned_data.get('root_cause_list')
                        root_cause_text = form.cleaned_data.get('root_cause_text')
                        root_cause_comment = form.cleaned_data.get('root_cause_comment')
                        if answer_date != "":
                            db_form.answer_date_fact = answer_date
                        else:
                            db_form.answer_date_fact = None
                        if answer_deadline != "":
                            db_form.answer_deadline_correct_fact = answer_deadline
                        else:
                            db_form.answer_deadline_correct_fact = None
                        if labor_costs_fact != "":
                            db_form.labor_costs_fact = labor_costs_fact
                        else:
                            db_form.labor_costs_fact = None
                        db_form.answer_remark = answer_remark
                        db_form.link_tech_name = link_tech_name
                        db_form.root_cause_list = root_cause_list
                        db_form.root_cause_text = root_cause_text
                        db_form.root_cause_comment = root_cause_comment
                        if db_form.comment != comment and comment != "":
                            d = datetime.now()
                            db_form.comment = comment + " (" + str(d.hour) + ':' + str(d.minute) + ':' + str(
                                d.second) + ' ' + str(d.day) + '.' + str(d.month) + '.' + str(d.year) + ' ' + shortName(
                                request.user) + ")"

                        db_form.save(
                            update_fields=['labor_costs_fact', 'answer_remark', 'link_tech_name', 'answer_date_fact',
                                           'answer_deadline_correct_fact', 'status', 'comment', 'root_cause_list',
                                           'root_cause_text', 'root_cause_comment'])
                        messages.success(request, "Изменения сохранены")
                    except Exception as e:
                        messages.error(request, "Возникла ошибка " + str(e))
                else:
                    print("ошибка в заполнении")
        else:
            form = FinalForm(db_form)
        if request.user == db_form.responsibleTrouble_name or db_form.responsibleTrouble_name in subs:
            next_step_key = True
        else:
            next_step_key = False
        return render(request, 'final.html', {'form': form,
                                              'gipcontext':
                                                  db_form.gip.last_name + ' ' +
                                                  db_form.gip.first_name,
                                              'rescontext':
                                                  db_form.responsibleTrouble_name.last_name + ' ' +
                                                  db_form.responsibleTrouble_name.first_name if db_form.responsibleTrouble_name else '',
                                              'exfcontext':
                                                  db_form.executor_fail_name.last_name + ' ' +
                                                  db_form.executor_fail_name.first_name if db_form.executor_fail_name else '',
                                              'excontext':
                                                  db_form.executor_name.last_name + ' ' +
                                                  db_form.executor_name.first_name if db_form.executor_name else '',
                                              'reestrID': db_form.reestrID.id,
                                              'remarkID': id,
                                              'customer': db_form.customer.name,
                                              'contract_number': db_form.project_dogovor.number,
                                              'reviewer': db_form.project_reviewer.name,
                                              'role': role,
                                              'next_step_key': next_step_key})
    else:
        return render(request, 'log_error.html', {'text': "Пожалуйста, авторизируйтесь, чтобы увидеть эту страницу."})


def remark(request, id):
    if request.user.is_authenticated:
        form = RemarkForm(reestr.objects.get(id=id))
        if request.user.groups.filter(name='Руководитель').exists():
            role = "Руководитель"
        elif request.user.groups.filter(name='Исполнитель').exists():
            role = "Исполнитель"
        elif request.user.groups.filter(name='Наблюдатель').exists():
            role = "Наблюдатель"
        else:
            role = "ГИП"
        return render(request, 'remark.html', {'form': form,
                                               'gipcontext':
                                                   reestr.objects.get(id=id).gip.last_name + ' ' +
                                                   reestr.objects.get(id=id).gip.first_name if reestr.objects.get(
                                                       id=id).gip else '',
                                               'rescontext':
                                                   reestr.objects.get(id=id).responsibleTrouble_name.last_name + ' ' +
                                                   reestr.objects.get(
                                                       id=id).responsibleTrouble_name.first_name if reestr.objects.get(
                                                       id=id).responsibleTrouble_name else '',
                                               'exfcontext':
                                                   reestr.objects.get(id=id).executor_fail_name.last_name + ' ' +
                                                   reestr.objects.get(
                                                       id=id).executor_fail_name.first_name if reestr.objects.get(
                                                       id=id).executor_fail_name else '',
                                               'excontext':
                                                   reestr.objects.get(id=id).executor_name.last_name + ' ' +
                                                   reestr.objects.get(
                                                       id=id).executor_name.first_name if reestr.objects.get(
                                                       id=id).executor_name else '',
                                               'remarkID': id,
                                               'status': reestr.objects.get(id=id).status,
                                               'role': role,
                                               'reestrID': reestr.objects.get(id=id).reestrID.id})
    else:
        return redirect("accounts/login/?next=/")


def close_remarks(request, id):
    if request.user.groups.filter(name='ГИП').exists():
        remarks = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) &
                    Q(status="На согласовании Рецензентом"))).order_by("num_remark")
        reest = reestInfo.objects.get(id=id)
        form = CloseForm()
        if request.method == 'POST':
            form = CloseForm(request.POST, request.FILES or None)
            if form.is_valid():
                form.save(commit=False)
                closed_remarks = form.cleaned_data['closed_remarks']
                cancel_remark_date = form.cleaned_data['cancel_remark_date']
                cancel_remark = form.cleaned_data['cancel_remark']
                sum = 0
                for upload in form.files.getlist("add_files"):
                    sum += upload.size
                if cancel_remark_date is None or cancel_remark == "":
                    form.add_error('cancel_remark_date', 'Пожалуйста, внесите данные')
                if sum > MAX_FILE_UPLOAD:
                    messages.error(request,
                                   'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                       sum))
                if cancel_remark_date is not None and cancel_remark != "" and sum <= MAX_FILE_UPLOAD:
                    try:
                        i = 0
                        IDnumber = ""
                        forClose = []
                        while i < len(closed_remarks):
                            if closed_remarks[i] not in ', ':
                                IDnumber += closed_remarks[i]
                            else:
                                if IDnumber != "":
                                    forClose.append(int(IDnumber))
                                IDnumber = ""
                            i += 1
                        if IDnumber != "":
                            forClose.append(int(IDnumber))
                        for r in remarks:
                            if r.id in forClose:
                                r.status = "Замечание снято"
                                r.cancel_remark = cancel_remark
                                r.cancel_remark_date = cancel_remark_date
                                r.save(update_fields=['status', 'cancel_remark', 'cancel_remark_date'])
                        step = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True))).exclude(status="Замечание снято"))
                        if step == 0:
                            reest.status = "Закрыт"
                            reest.save(update_fields=['status'])
                        name = form.cleaned_data.get("file_name")
                        comment = form.cleaned_data.get("file_comment")
                        form.save_files(reest, name, comment)
                        messages.success(request, "Изменения сохранены")
                    except Exception:
                        messages.error(request, "Возникла ошибка")
            else:
                cancel_remark_date = form.cleaned_data['cancel_remark_date']
                cancel_remark = form.cleaned_data['cancel_remark']
                if cancel_remark_date is None or cancel_remark == "":
                    form.add_error('cancel_remark_date', 'Пожалуйста, внесите данные')
        return render(request, 'close_remarks.html', {'remarks': remarks, 'reest': reest, 'form': form})
    else:
        return render(request, 'log_error.html',
                      {'text': "Пожалуйста, авторизируйтесь в качестве ГИПа, чтобы увидеть эту страницу."})


def return_remarks(request, id):
    if request.user.groups.filter(name='ГИП').exists():
        remarks = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True) &
                    Q(status="На согласовании Рецензентом"))).order_by("num_remark")
        reest = reestInfo.objects.get(id=id)
        form = ReturnForm()
        if request.method == 'POST':
            form = ReturnForm(request.POST, request.FILES or None)
            if form.is_valid():
                # form.save(commit=False)
                returned_remarks = form.cleaned_data['returned_remarks']
                sum = 0
                for upload in form.files.getlist("add_files"):
                    sum += upload.size
                if sum <= MAX_FILE_UPLOAD:
                    try:
                        i = 0
                        IDnumber = ""
                        forClose = []
                        while i < len(returned_remarks):
                            if returned_remarks[i] not in ', ':
                                IDnumber += returned_remarks[i]
                            else:
                                if IDnumber != "":
                                    forClose.append(int(IDnumber))
                                IDnumber = ""
                            i += 1
                        if IDnumber != "":
                            forClose.append(int(IDnumber))
                        step = 0
                        for r in remarks:
                            if r.id in forClose:
                                r.actuality = False
                                r.save(update_fields=['actuality'])
                                reestr.objects.create(reestrID=r.reestrID,
                                                      customer=r.customer,
                                                      project_dogovor=r.project_dogovor,
                                                      project_date_contract=r.project_date_contract,
                                                      project_name=r.project_name,
                                                      gip=r.gip,
                                                      project_reviewer=r.project_reviewer,
                                                      out_mail_num=r.out_mail_num,
                                                      out_mail_date=r.out_mail_date,
                                                      in_mail_num=r.in_mail_num,
                                                      in_mail_date=r.in_mail_date,
                                                      num_reestr=r.num_reestr,
                                                      num_remark=r.num_remark,
                                                      designation_name=r.designation_name,
                                                      section_name=r.section_name,
                                                      remark_name=r.remark_name,
                                                      rational=r.rational,
                                                      status="На заполнении ГИПом",
                                                      remark_v=r.remark_v + 1,
                                                      answer_remark=r.answer_remark,
                                                      comment=r.comment)
                                step += 1
                            elif r.status != "На согласовании Рецензентом":
                                step += 1
                        if step == len(remarks):
                            reest.status = "На доработке"
                        reest.save(update_fields=['status'])
                        name = form.cleaned_data.get("file_name")
                        comment = form.cleaned_data.get("file_comment")
                        dateValue = form.cleaned_data.get("date_field")
                        reest.end_date = workDays(dateValue, 9)
                        reest.save(update_fields=['end_date'])
                        form.save_files(reest, name, comment, dateValue)
                        messages.success(request, "Изменения сохранены")
                    except Exception:
                        messages.error(request, "Возникла ошибка ")
                else:
                    messages.error(request,
                                   'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                       sum))
        return render(request, 'return_remarks.html', {'remarks': remarks, 'reest': reest, 'form': form})
    else:
        return render(request, 'log_error.html',
                      {'text': "Пожалуйста, авторизируйтесь в качестве ГИПа, чтобы увидеть эту страницу."})


def import_remark(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(name='Наблюдатель').exists():
        reest = reestInfo.objects.get(id=id)
        form = RemarkFileForm()
        if request.method == 'POST':
            form = RemarkFileForm(request.POST, request.FILES or None)
            if form.is_valid():
                try:
                    sum = 0
                    for upload in form.files.getlist("file"):
                        sum += upload.size
                    if form.cleaned_data['file'] and sum <= MAX_FILE_UPLOAD:
                        auto_import(form.cleaned_data['file'], reest)
                        step = len(reestr.objects.filter((Q(reestrID=id) & Q(actuality=True))).exclude(status="Замечание снято"))
                        if step == 0:
                            reest.status = "Закрыт"
                            reest.save(update_fields=['status'])
                        form.save(commit=False)
                        name = form.cleaned_data.get("file_name")
                        comment = form.cleaned_data.get("comment")
                        form.save_files(reest, name, comment)
                        messages.success(request, "Замечания обработаны")
                    elif sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(
                                           sum))
                    else:
                        messages.error(request, "Загрузите файл")
                except Exception as e:
                    messages.error(request, "Возникла ошибка "+str(e))
        return render(request, 'import_remark.html', {'reest': reest, 'form': form})
    else:
        return render(request, 'log_error.html',
                      {
                          'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или Наблюдателя, чтобы увидеть эту страницу."})

def export_remark(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(name='Наблюдатель').exists():
        reest = reestInfo.objects.get(id=id)
        form = RemarkFileForm()
        if request.method == 'POST':
            form = RemarkFileForm(request.POST, request.FILES or None)
            if form.is_valid():
                try:
                    sum = 0
                    for upload in form.files.getlist("file"):
                        sum += upload.size
                    if form.cleaned_data['file'] and sum <= MAX_FILE_UPLOAD:
                        form.save(commit=False)
                        name = ''
                        comment = ''
                        file_name = form.save_files(reest, name, comment)
                        auto_export(file_name, reest)
                        response = FileResponse(open(os.path.join(MEDIA_ROOT, str(file_name)), 'rb'), as_attachment=True)
                        return response
                        #messages.error(request, str(lens))
                    elif sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(sum))
                    else:
                        messages.error(request, "Загрузите файл")
                except Exception as e:
                    messages.error(request, "Возникла ошибка "+str(e))
        return render(request, 'export_remark.html', {'reest': reest, 'form': form})
    else:
        return render(request, 'log_error.html',
                      {
                          'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или Наблюдателя, чтобы увидеть эту страницу."})
def planner_link(request, id):
    if request.user.is_authenticated:
        reest = reestInfo.objects.get(id=id)
        form = RemarkFileForm()
        if request.method == 'POST':
            form = RemarkFileForm(request.POST, request.FILES or None)
            if form.is_valid():
                try:
                    sum = 0
                    for upload in form.files.getlist("file"):
                        sum += upload.size
                    if form.cleaned_data['file'] and sum <= MAX_FILE_UPLOAD:
                        form.save(commit=False)
                        name = ''
                        comment = ''
                        file_name = form.save_files(reest, name, comment)
                        xlsxPlanner(file_name, reest)
                        response = FileResponse(open(os.path.join(MEDIA_ROOT, str(file_name)), 'rb'), as_attachment=True)
                        return response
                    elif sum > MAX_FILE_UPLOAD:
                        messages.error(request,
                                       'Объём загружаемых файлов не должен превышать 30 МБ, объём Ваших файлов составляет ' + getHumanReadable(sum))
                    else:
                        messages.error(request, "Загрузите файл")
                except Exception as e:
                    messages.error(request, "Возникла ошибка "+str(e))
        return render(request, 'planner_link.html', {'reest': reest, 'form': form})
    else:
        return render(request, 'log_error.html',
                      {
                          'text': "Пожалуйста, авторизируйтесь в качестве сотрудника производственного отдела, чтобы увидеть эту страницу."})

def aiGIP(request, sessionKey):
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(name='Наблюдатель').exists() or request.user.is_authenticated:
        realtime = timezone.now()
        userID = request.user
        try:
            session = aiChatSession.objects.get(session_key=sessionKey)
            chat_messages = aiChatMessage.objects.filter(session=session)
        except Exception:
            session = None
            chat_messages = []
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                user_message = data.get('message', 'нет сообщения')
                # сохранение полученного сообщения в БД
                print(user_message)
                session, created = aiChatSession.objects.update_or_create(user=userID, session_key=sessionKey)
                aiChatMessage.objects.create(session=session, role='user', content=user_message, timestamp=realtime)
                # логика ответа на основные запросы
                answer_message = 'Кажется, Ваш запрос сформулирован неполно'
                if "Найди записи похожие на замечания из реестра" in user_message and "[" not in user_message:
                    numReestr = ""
                    i = 44
                    while user_message[i] not in "0123456789-" and i < len(user_message)-1:
                        i += 1
                    while user_message[i] in "0123456789-" and i < len(user_message)-1:
                        numReestr = numReestr + user_message[i]
                        i += 1
                    if user_message[-1] in "0123456789-":
                        numReestr = numReestr + user_message[-1]
                    reestr_index = '110/' + numReestr[:5] + 'Д_' + numReestr[5:]
                    session.context['запрошенный реестр'] = reestr_index
                    reest = reestInfo.objects.get(reestr_index=reestr_index)
                    remarks = reestr.objects.filter(reestrID=reest)
                    session.context['запрошенные замечания'] = [i.remark_index for i in remarks]
                    query_remarks = [i.remark_name for i in remarks]
                    print(query_remarks)
                    answer_message = 'Поиск по всем замечаниям в реестре ' + numReestr
                elif "Найди записи похожие на замечания" in user_message and "[" not in user_message:
                    numRemarks = []
                    i = 33
                    while user_message[i] != "и" and i < len(user_message)-1:
                        if user_message[i] not in " ,":
                            numRemarks[-1] = numRemarks[-1] + user_message[i]
                        elif i != len(user_message):
                            numRemarks.append("")
                        i += 1
                    if i == len(user_message)-1 and user_message[-1] in "0123456789-.н":
                        numRemarks[-1] = numRemarks[-1] + user_message[-1]
                    numReestr = ""
                    if user_message[i] == "и":
                        while user_message[i] not in "0123456789-" and i < len(user_message)-1:
                            i += 1
                        while user_message[i] in "0123456789-" and i < len(user_message) - 1:
                            numReestr = numReestr + user_message[i]
                            i += 1
                        if user_message[-1] in "0123456789-":
                            numReestr = numReestr + user_message[-1]
                    answer_message = 'Поиск по замечаниям'
                    for i in numRemarks:
                        answer_message += " " + i
                    answer_message += " в реестре " + numReestr
                elif "Выгрузи всё что нашлось" in user_message and "[" not in user_message:
                    i = 36
                    while user_message[i] not in '0123456789.-н' and i < len(user_message) - 1:
                        i += 1
                    numRemarks = [""]
                    while i < len(user_message) - 1:
                        if user_message[i] not in " ,":
                            numRemarks[-1] = numRemarks[-1] + user_message[i]
                        elif i != len(user_message):
                            numRemarks.append("")
                        i += 1
                    if i == len(user_message) - 1 and user_message[-1] in "0123456789-.н":
                        numRemarks[-1] = numRemarks[-1] + user_message[-1]
                    answer_message = 'Результаты для замечаний'
                    for i in numRemarks:
                        answer_message += " " + i
                elif "Выгрузи замечания" in user_message and "[" not in user_message:
                    i = 29
                    while user_message[i] not in '0123456789-' and i < len(user_message) - 1:
                        i += 1
                    numReestrs = [""]
                    while i < len(user_message) - 1:
                        if user_message[i] not in " ,":
                            numReestrs[-1] = numReestrs[-1] + user_message[i]
                        elif i != len(user_message):
                            numReestrs.append("")
                        i += 1
                    if i == len(user_message) - 1 and user_message[-1] in "0123456789-":
                        numReestrs[-1] = numReestrs[-1] + user_message[-1]
                    answer_message = 'Результаты для замечаний из реестров'
                    for i in numReestrs:
                        answer_message += " " + i
                elif "Выгрузи всё что нашёл" in user_message:
                    answer_message = 'Все результаты'
                elif "Выгрузи" in user_message and "[" not in user_message:
                    i = 7
                    while user_message[i] not in '0123456789' and i < len(user_message) - 1:
                        i += 1
                    countRemarks = ""
                    while user_message[i] in '0123456789' and i < len(user_message) - 1:
                        countRemarks = countRemarks + user_message[i]
                        i += 1
                    answer_message = "Первые " + countRemarks + " замечаний"
                realtime = timezone.now()
                aiChatMessage.objects.create(session=session, role='assistant', content=answer_message, timestamp=realtime)
                session.save()
                return JsonResponse({
                    'response': answer_message,
                    'status': 'ok'
                })
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print("Ошибка ", e, exc_tb.tb_lineno)
                return JsonResponse({
                    'error': 'server',
                    'details': str(e)
                }, status=500)
        return render(request, 'AI_GIP.html', {'current_time': realtime, 'sessionKey': sessionKey, 'chat_messages': chat_messages})
    else:
        return render(request, 'log_error.html',
                      {
                          'text': "Пожалуйста, авторизируйтесь в качестве ГИПа или Наблюдателя, чтобы увидеть эту страницу."})

def status(request, id):
    if request.user.groups.filter(name='ГИП').exists() or request.user.groups.filter(name='Наблюдатель').exists() or request.user.is_superuser:
        remarks = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True))).annotate(
            remark_priority_order=remark_priority_order,
            custom_string_order=Length('num_remark')).order_by('remark_priority_order', 'custom_string_order', 'num_remark')
        reest = reestInfo.objects.get(id=id)
        max_remark_num = 0
        max_remark_point_num = 0
        for i in remarks:
            if '.' not in i.num_remark:
                if len(i.num_remark) > max_remark_num:
                    max_remark_num = len(i.num_remark)
            else:
                point_idx = i.num_remark.find('.')
                if len(i.num_remark[:point_idx]) > max_remark_num:
                    max_remark_num = len(i.num_remark[:point_idx])
                if len(i.num_remark[point_idx + 1:]) > max_remark_point_num:
                    max_remark_point_num = len(i.num_remark[point_idx + 1:])
        if request.method == 'POST':
            chosen_status = request.POST.get("chosen_status")
            chosen_remarks = request.POST.get("chosen_remarks")
            if chosen_status == '':
                messages.error(request, "Выберите новый статус")
            if chosen_remarks == '':
                messages.error(request, "Должно быть выбрано хотя бы одно замечание")
            if chosen_remarks != '' and chosen_status != '':
                i = 0
                IDnumber = ""
                forChange = []
                while i < len(chosen_remarks):
                    if chosen_remarks[i] not in ', ':
                        IDnumber += chosen_remarks[i]
                    else:
                        if IDnumber != "":
                            forChange.append(int(IDnumber))
                        IDnumber = ""
                    i += 1
                if IDnumber != "":
                    forChange.append(int(IDnumber))
                for i in forChange:
                    remark = reestr.objects.get(id=i)
                    remark.status = chosen_status
                    remark.save(update_fields=['status'])
                remarks = reestr.objects.filter((Q(reestrID=id) & Q(actuality=True))).annotate(
                    remark_priority_order=remark_priority_order,
                    custom_string_order=Length('num_remark')).order_by('remark_priority_order', 'custom_string_order', 'num_remark')
                confirmed = True
                closed = True
                returned = True
                reest_status = "Формирование"
                for r in remarks:
                    if r.status not in ["На согласовании ГИПом", "Принято ГИПом", "Согласовано ГИПом"]:
                        confirmed = False
                    if r.status != "Замечание снято":
                        closed = False
                    if "На доработке" not in r.status:
                        returned = False
                    if "На заполнении" in r.status or r.status == "На согласовании руководителем":
                        reest_status = "На заполнении"
                    if "Подготовка ответов" in r.status:
                        reest_status = "Подготовка ответов"
                    if r.status == "На согласовании Рецензентом":
                        reest_status = "На согласовании Рецензентом"
                if confirmed:
                    reest_status = "На согласовании"
                if returned:
                    reest_status = "На доработке"
                if closed:
                    reest_status = "Закрыт"
                reest.status = reest_status
                reest.save(update_fields=['status'])
        return render(request, 'status.html', {'remarks': remarks,
                                                                   'reest': reest,
                                                                   'max_remark_num': max_remark_num,
                                                                   'max_remark_point_num': max_remark_point_num})
    else:
        return render(request, 'log_error.html',
                      {'text': "Пожалуйста, авторизируйтесь в качестве ГИПа, чтобы увидеть эту страницу."})