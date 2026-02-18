from django import forms
from formapp.models import reestr, reestInfo, files, customers, reviewers, contracts, departments
from django.contrib.auth.models import User
from django.db.models import Q, When, Value, Case
from datetime import date
from django.contrib.admin.widgets import AdminDateWidget
from formapp.functions import workDays, getHumanReadable, shortName
import numpy as np
import os


# CHOICES_YEARS = [('$__all', '-----')]
# for j in np.unique(np.array([i.in_mail_date.year for i in reestr.objects.all()])):
# CHOICES_YEARS.append((j, j))
# CHOICES_GIPS = [('$__all', '-----')]
# for i in User.objects.filter(groups=1).order_by('last_name'):
# CHOICES_GIPS.append((i.id, shortName(i)))
# CHOICES_REVIEWERS = [('$__all', '-----')]
# for i in reviewers.objects.all().order_by('name'):
# CHOICES_REVIEWERS.append((i.id, i.name))
# CHOICES_CUSTOMERS = [('$__all', '-----')]
# for i in customers.objects.all().order_by('name'):
# CHOICES_CUSTOMERS.append((i.id, i.name))
# CHOICES_CONTRACTS = [('$__all', '-----')]
# for i in contracts.objects.all().order_by('number'):
# CHOICES_CONTRACTS.append((i.id, i.number))
# CHOICES_REESTRS = [('$__all', '-----')]
# for i in reestInfo.objects.all():
# CHOICES_REESTRS.append((i.id, i.project_dogovor.number[4:9]+i.num_reestr))
# CHOICES_IMPORTANCE = [('$__all', '-----'), ('Существенное', 'Существенное'), ('Несущественное', 'Несущественное'), ('В компетенции Заказчика', 'В компетенции Заказчика')]
# CHOICES_RESPONS = [('н', '-----'), ('ущественное', 'Исполнитель'), ('Заказчик', 'Заказчик')]
# CHOICES_DEPARTMENTS = [('$__all', '-----')]
# for j in np.unique(np.array([i.department for i in departments.objects.all()])):
# CHOICES_DEPARTMENTS.append((j, j))

class FileForm(forms.ModelForm):
    class Meta:
        model = files
        fields = ('file', 'file_name', 'comment')
        widgets = {
            'file': forms.ClearableFileInput(attrs={"multiple": True}),
            'file_name': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'comment': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'})
        }

    def save_files(self, reestr, name, comment):
        for upload in self.files.getlist("file"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr)
            add_file.save()


class RemarkFileForm(forms.ModelForm):
    class Meta:
        model = files
        fields = ('file', 'file_name', 'comment')
        error_messages = {
            'file': {'required': "Пожалуйста, внесите данные"}
        }
        widgets = {
            'file': forms.ClearableFileInput(attrs={"multiple": False, 'required': 'required'}),
            'file_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'value': 'Файл замечаний от ФАУ "Главгосэкспертиза России"'}),
            'comment': forms.Textarea(attrs={'class': 'form-readonly'})
        }

    def save_files(self, reest, name, comment):
        for upload in self.files.getlist("file"):
            add_file = files(reestr=reest, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reest.project_dogovor.number[4:9] + reest.num_reestr)
            add_file.save()
            return add_file


class ReestrForm(forms.ModelForm):
    class Meta:
        model = reestInfo
        fields = ('customer', 'gip', 'project_dogovor', 'project_date_contract', 'project_name', 'project_reviewer',
                  'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date', 'num_reestr', 'start_date',
                  'end_date', 'status')
        error_messages = {
            'customer': {'required': 'Пожалуйста, внесите данные', },
            'project_dogovor': {'required': 'Пожалуйста, внесите данные', },
            'project_name': {'required': 'Пожалуйста, внесите данные', },
            'project_reviewer': {'required': 'Пожалуйста, внесите данные', },
            'out_mail_num': {'required': 'Пожалуйста, внесите данные', },
            'in_mail_num': {'required': 'Пожалуйста, внесите данные', },
            'out_mail_date': {'required': 'Пожалуйста, внесите данные', },
            'in_mail_date': {'required': 'Пожалуйста, внесите данные', },
            'num_reestr': {'required': 'Пожалуйста, внесите данные', },
            'project_date_contract': {'required': 'Пожалуйста, внесите данные', },
            'gip': {'required': 'Пожалуйста, внесите данные', },
        }
        widgets = {
            'project_date_contract': forms.DateInput(
                attrs={'class': 'form-importance', 'required': 'required', 'readonly': 'readonly', 'type': 'date'}),
            'project_name': forms.TextInput(
                attrs={'class': 'form-importance', 'readonly': 'readonly', 'required': 'required'}),
            'out_mail_num': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'required': 'required'}),
            'out_mail_date': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year) + '-12-31'}),
            'in_mail_num': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'placeholder': '110/1234',
                       'required': 'required'}),
            'in_mail_date': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year) + '-12-31'}),
            'num_reestr': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'required': 'required'}),
            'start_date': forms.DateInput(attrs={'value': date.today()}),
            'end_date': forms.DateInput(attrs={'value': workDays(date.today(), 9)}),
        }

    customer = forms.ModelChoiceField(queryset=customers.objects.all().order_by('name'), empty_label='-----',
                                      widget=forms.Select(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                      error_messages={'required': 'Пожалуйста, внесите данные'})
    project_reviewer = forms.ModelChoiceField(queryset=reviewers.objects.all().order_by('name'), empty_label='-----',
                                              widget=forms.Select(
                                                  attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                              error_messages={'required': 'Пожалуйста, внесите данные'})
    project_dogovor = forms.ModelChoiceField(queryset=contracts.objects.all().order_by('number'), empty_label='-----',
                                             widget=forms.Select(
                                                 attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                             error_messages={'required': 'Пожалуйста, внесите данные'})
    gip = forms.ModelChoiceField(queryset=User.objects.filter(groups=1).order_by('last_name'), empty_label='-----',
                                 widget=forms.Select(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                 error_messages={'required': 'Пожалуйста, внесите данные'})
    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=False)
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=False)
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].initial = 'Формирование'
        self.fields['start_date'].initial = date.today()
        self.fields['end_date'].initial = workDays(date.today(), 9)

    def save_files(self, reestr, name, comment):
        for upload in self.files.getlist("add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr)
            add_file.save()


class RemarkForm(forms.ModelForm):
    class Meta:
        model = reestr
        fields = ('customer', 'project_dogovor', 'project_date_contract', 'project_name', 'project_reviewer',
                  'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date', 'num_reestr', 'num_remark',
                  'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name', 'answer_date_plan',
                  'answer_date_fact', 'answer_deadline_correct_plan', 'answer_deadline_correct_fact',
                  'labor_costs_plan',
                  'labor_costs_fact', 'comment', 'answer_remark', 'link_tech_name', 'cancel_remark', 'total_importance',
                  'root_cause_list', 'root_cause_text', 'root_cause_comment', 'executor_fail_text', 'reestrID',
                  'importance1', 'importance2', 'importance3', 'importance4',
                  'importance5', 'importance6', 'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment')
        widgets = {
            'customer': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_dogovor': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_reviewer': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'rational': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: ТХ'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'title': 'Пример: 099-3053-1001624-ТХ', 'readonly': 'readonly'}),

            'answer_date_plan': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'answer_date_fact': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'answer_deadline_correct_plan': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'answer_deadline_correct_fact': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'labor_costs_plan': forms.NumberInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'labor_costs_fact': forms.NumberInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-readonly', 'title': 'Указывается информация о статусе замечания',
                       'readonly': 'readonly'}),
            'answer_remark': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'link_tech_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'cancel_remark': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'importance1': forms.RadioSelect(choices=[(True, 'Да'), (False, 'Нет')], attrs={'readonly': 'readonly'}),
            'importance2': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance3': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance4': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance5': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance6': forms.RadioSelect(
                choices=[(True, 'Вина/Инициатива Заказчика'), (False, 'Вина проектировщика')],
                attrs={'readonly': 'readonly'}),
            'importance7': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'imp3_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'imp4_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'imp7_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'total_importance': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly',
                                                       'placeholder': '', 'id': 'total_imp'}),
            'root_cause_list': forms.TextInput(
                attrs={'class': 'form-readonly', 'id': 'root_cause', 'readonly': 'readonly'}),
            'root_cause_text': forms.Textarea(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'id': 'root_cause'}),
            'root_cause_comment': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'id': 'executor_fail_text'}),
        }

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reestrID'].initial = reest.reestrID
        self.fields['customer'].initial = reest.customer.name
        self.fields['project_dogovor'].initial = reest.project_dogovor.number
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['project_reviewer'].initial = reest.project_reviewer.name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['answer_date_plan'].initial = reest.answer_date_plan
        self.fields['answer_deadline_correct_plan'].initial = reest.answer_deadline_correct_plan
        self.fields['labor_costs_plan'].initial = reest.labor_costs_plan
        self.fields['answer_date_fact'].initial = reest.answer_date_fact
        self.fields['answer_deadline_correct_fact'].initial = reest.answer_deadline_correct_fact
        self.fields['labor_costs_fact'].initial = reest.labor_costs_fact
        self.fields['comment'].initial = reest.comment
        self.fields['answer_remark'].initial = reest.answer_remark
        self.fields['link_tech_name'].initial = reest.link_tech_name
        self.fields['total_importance'].initial = reest.total_importance
        self.fields['root_cause_list'].initial = reest.root_cause_list
        self.fields['root_cause_text'].initial = reest.root_cause_text
        self.fields['root_cause_comment'].initial = reest.root_cause_comment
        self.fields['executor_fail_text'].initial = reest.executor_fail_text
        self.fields['importance1'].initial = reest.importance1
        self.fields['importance2'].initial = reest.importance2
        self.fields['importance3'].initial = reest.importance3
        self.fields['importance4'].initial = reest.importance4
        self.fields['importance5'].initial = reest.importance5
        self.fields['importance6'].initial = reest.importance6
        self.fields['importance7'].initial = reest.importance7
        self.fields['imp3_comment'].initial = reest.imp3_comment
        self.fields['imp4_comment'].initial = reest.imp4_comment
        self.fields['imp7_comment'].initial = reest.imp7_comment
        if reest.cancel_remark:
            self.fields['cancel_remark'].initial = reest.cancel_remark + " от " + str(reest.cancel_remark_date)


class GIPform(forms.ModelForm):
    class Meta:
        model = reestr
        fields = ('reestrID', 'customer', 'gip', 'responsibleTrouble_name', 'project_dogovor', 'project_date_contract',
                  'project_name', 'project_reviewer',
                  'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date', 'num_reestr', 'num_remark',
                  'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name', 'status', 'comment')
        error_messages = {
            'customer': {'required': 'Пожалуйста, внесите данные', },
            'project_dogovor': {'required': 'Пожалуйста, внесите данные', },
            'project_name': {'required': 'Пожалуйста, внесите данные', },
            'gip': {'required': 'Пожалуйста, внесите данные', },
            'project_reviewer': {'required': 'Пожалуйста, внесите данные', },
            'out_mail_num': {'required': 'Пожалуйста, внесите данные', },
            'in_mail_num': {'required': 'Пожалуйста, внесите данные', },
            'num_reestr': {'required': 'Пожалуйста, внесите данные', },
            'num_remark': {'required': 'Пожалуйста, внесите данные', },
            'remark_name': {'required': 'Пожалуйста, внесите данные', },
            'rational': {'required': 'Пожалуйста, внесите данные', },
            'designation_name': {'required': 'Пожалуйста, внесите данные', },
            'section_name': {'required': 'Пожалуйста, внесите данные', },
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'rational': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'title': 'Пример: ТХ', 'autocomplete': 'off'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'title': 'Пример: 099-3053-1001624-ТХ', 'autocomplete': 'off'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания',
                       'autocomplete': 'off', 'id': 'comment'}),
        }

    customer = forms.ModelChoiceField(queryset=customers.objects.all().order_by('name'), empty_label='-----',
                                      widget=forms.Select(attrs={'hidden': 'hidden'}))
    project_reviewer = forms.ModelChoiceField(queryset=reviewers.objects.all().order_by('name'), empty_label='-----',
                                              widget=forms.Select(attrs={'hidden': 'hidden'}))
    project_dogovor = forms.ModelChoiceField(queryset=contracts.objects.all().order_by('number'), empty_label='-----',
                                             widget=forms.Select(attrs={'hidden': 'hidden'}))
    gip = forms.ModelChoiceField(queryset=User.objects.filter(groups=1).order_by('last_name'), empty_label='-----',
                                 widget=forms.Select(attrs={'hidden': 'hidden'}))
    responsibleTrouble_name = forms.ModelChoiceField(
        queryset=User.objects.filter((Q(groups=1) | Q(groups=2))).order_by('last_name'), empty_label='-----',
        widget=forms.Select(attrs={'class': 'form-textinput', 'autocomplete': 'off'}), required=False)
    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=False)
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=False)
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=False)
    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reest = reestr.objects.all()
        # reest = reestr.objects.all().last()
        self.fields['reestrID'].initial = reest.id
        self.fields['customer'].initial = reest.customer
        self.fields['project_dogovor'].initial = reest.project_dogovor
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['gip'].initial = reest.gip
        self.fields['project_reviewer'].initial = reest.project_reviewer
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['status'].initial = 'Формирование'

    def save_files(self, reestr, name, comment, cause_name, cause_comment, remark):
        for upload in self.files.getlist("add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=cause_name,
                             comment=cause_comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class GIPform1(forms.ModelForm):
    class Meta:
        model = reestr
        fields = ('reestrID', 'responsibleTrouble_name', 'project_name', 'project_date_contract',
                  'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date', 'num_reestr', 'num_remark',
                  'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name', 'status', 'comment',
                  'answer_remark')
        error_messages = {
            'project_name': {'required': 'Пожалуйста, внесите данные', },
            'out_mail_num': {'required': 'Пожалуйста, внесите данные', },
            'in_mail_num': {'required': 'Пожалуйста, внесите данные', },
            'num_reestr': {'required': 'Пожалуйста, внесите данные', },
            'num_remark': {'required': 'Пожалуйста, внесите данные', },
            'remark_name': {'required': 'Пожалуйста, внесите данные', },
            'rational': {'required': 'Пожалуйста, внесите данные', },
            'designation_name': {'required': 'Пожалуйста, внесите данные', },
            'section_name': {'required': 'Пожалуйста, внесите данные', },
            'responsibleTrouble_name': {'required': 'Пожалуйста, внесите данные', },
            'comment': {'required': ""},
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'rational': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'title': 'Пример: ТХ', 'autocomplete': 'off'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'title': 'Пример: 099-3053-1001624-ТХ', 'autocomplete': 'off'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания',
                       'autocomplete': 'off', 'id': 'comment'}),
            'answer_remark': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        }

    responsibleTrouble_name = forms.ModelChoiceField(
        queryset=User.objects.filter((Q(groups=1) | Q(groups=2))).order_by('last_name'), empty_label='-----',
        widget=forms.Select(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
        error_messages={'required': 'Пожалуйста, внесите данные'})
    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=False)
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=False)
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=False)
    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, remark, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reestrID'].initial = remark.reestrID
        self.fields['project_date_contract'].initial = remark.project_date_contract
        self.fields['project_name'].initial = remark.project_name
        self.fields['out_mail_num'].initial = remark.out_mail_num
        self.fields['out_mail_date'].initial = remark.out_mail_date
        self.fields['in_mail_num'].initial = remark.in_mail_num
        self.fields['in_mail_date'].initial = remark.in_mail_date
        self.fields['num_reestr'].initial = remark.num_reestr
        self.fields['status'].initial = remark.status
        self.fields['num_remark'].initial = remark.num_remark
        self.fields['designation_name'].initial = remark.designation_name
        self.fields['section_name'].initial = remark.section_name
        self.fields['remark_name'].initial = remark.remark_name
        self.fields['rational'].initial = remark.rational
        self.fields['remark_v'].initial = remark.remark_v
        self.fields['comment'].initial = remark.comment
        if reestInfo.objects.get(
                id=remark.reestrID.id).status == "На согласовании Рецензентом" or reestInfo.objects.get(
                id=remark.reestrID.id).status == "На доработке":
            self.fields['answer_remark'].initial = remark.answer_remark

    def save_files(self, reestr, name, comment, cause_name, cause_comment, remark):
        for upload in self.files.getlist("add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=cause_name,
                             comment=cause_comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class BossForm1(forms.ModelForm):
    class Meta:
        model = reestr
        fields = (
        'project_date_contract', 'project_name', 'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date',
        'num_reestr', 'num_remark', 'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name',
        'executor_fail_name', 'executor_name', 'comment', 'status', 'executor_fail_text', 'answer_remark')
        error_messages = {
            'executor_fail_name': {'required': "Пожалуйста, внесите данные"},
            'executor_fail_text': {'required': ""},
            'executor_name': {'required': "Пожалуйста, внесите данные"},
            'comment': {'required': ""},
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'rational': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: ТХ'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: 099-3053-1001624-ТХ'}),
            'add_files': forms.ClearableFileInput(),

            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'executor_fail_text',
                       'hidden': 'hidden'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания',
                       'autocomplete': 'off', 'id': 'comment'}),
            'answer_remark': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        }

    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reest = reestr.objects.all()
        # reest = reestr.objects.all().last()
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['status'].initial = reest.status
        self.fields['comment'].initial = reest.comment

        if reestInfo.objects.get(id=reest.reestrID.id).status == "На согласовании Рецензентом" or reestInfo.objects.get(
                id=reest.reestrID.id).status == "На доработке":
            self.fields['answer_remark'].initial = reest.answer_remark

        q1 = (Q(groups=1) | Q(groups=2) | Q(groups=3)) & Q(
            departments__department=reest.responsibleTrouble_name.departments.department)
        q2 = Q(groups=4)
        q3 = Q(username="emptyUSER")
        qs = User.objects.filter(q1 | q2 | q3).annotate(
            search_type_ordering=Case(When(q3, Value(2)), When(q1, then=Value(1)), When(q2, then=Value(0)),
                                      default=Value(-1))).order_by('-search_type_ordering', 'last_name')
        self.fields['executor_fail_name'] = forms.ModelChoiceField(queryset=qs,
                                                                   empty_label='-----', required=False,
                                                                   widget=forms.Select(
                                                                       attrs={'class': 'form-textinput',
                                                                              'autocomplete': 'off'}),
                                                                   error_messages={
                                                                       'required': 'Пожалуйста, внесите данные'})
        qs = User.objects.filter(q1 | q2).annotate(
            search_type_ordering=Case(When(q1, then=Value(1)), When(q2, then=Value(0)), default=Value(-1))).order_by(
            '-search_type_ordering', 'last_name')
        self.fields['executor_name'] = forms.ModelChoiceField(queryset=qs,
                                                              empty_label='-----',
                                                              widget=forms.Select(
                                                                  attrs={'class': 'form-textinput',
                                                                         'autocomplete': 'off'}),
                                                              error_messages={'required': 'Пожалуйста, внесите данные'})

    def save_files(self, reestr, name, comment, remark):
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name,
                             comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class emplForm(forms.ModelForm):
    class Meta:
        model = reestr
        fields = (
        'project_date_contract', 'project_name', 'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date',
        'num_reestr', 'num_remark', 'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name',
        'answer_date_plan', 'answer_deadline_correct_plan', 'executor_fail_text',
        'labor_costs_plan', 'comment', 'answer_remark', 'total_importance', 'root_cause_list',
        'root_cause_comment', 'root_cause_text', 'status', 'importance1', 'importance2', 'importance3', 'importance4',
        'importance5', 'importance6', 'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment')
        error_messages = {
            'answer_date_plan': {'required': "Пожалуйста, внесите данные"},
            'answer_deadline_correct_plan': {'required': "Пожалуйста, внесите данные"},
            'labor_costs_plan': {'required': "Пожалуйста, внесите данные"},
            'comment': {'required': "Пожалуйста, внесите данные"},
            'answer_remark': {'required': "Пожалуйста, внесите данные"},
            'total_importance': {'required': "Пожалуйста, внесите данные"},
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'rational': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: ТХ'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: 099-3053-1001624-ТХ'}),
            'add_files': forms.ClearableFileInput(),
            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'id': 'executor_fail_text',
                       'hidden': 'hidden'}),

            'answer_date_plan': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'answer_deadline_correct_plan': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'labor_costs_plan': forms.NumberInput(
                attrs={'minlength': 3, 'required': 'required', 'class': 'form-textinput', 'step': '0.05', 'min': '0.1',
                       'autocomplete': 'off'}),
            'comment': forms.Textarea(attrs={'required': 'required', 'class': 'form-textinput',
                                             'title': 'Указывается информация о статусе замечания',
                                             'autocomplete': 'off'}),
            'answer_remark': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'importance1': forms.RadioSelect(choices=[(True, 'Да'), (False, 'Нет')]),
            'importance2': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance3': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance4': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance5': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance6': forms.RadioSelect(
                choices=[(True, 'Вина/Инициатива Заказчика'), (False, 'Вина проектировщика')]),
            'importance7': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'imp3_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'imp4_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'imp7_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'total_importance': forms.TextInput(
                attrs={'required': 'required', 'class': 'form-importance', 'readonly': 'readonly', 'placeholder': '',
                       'id': 'total_imp'}),
            'root_cause_list': forms.TextInput(
                attrs={'class': 'form-textinput', 'id': 'root_cause'}),
            'root_cause_text': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'root_cause0', 'hidden': 'hidden'}),
            'root_cause_comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'})
        }

    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['status'].initial = reest.status
        self.fields['executor_fail_text'].initial = reest.executor_fail_text

        if reest.answer_date_plan:
            self.fields['answer_date_plan'].initial = str(reest.answer_date_plan)
        if reest.answer_deadline_correct_plan:
            self.fields['answer_deadline_correct_plan'].initial = str(reest.answer_deadline_correct_plan)
        try:
            department = departments.objects.get(user=reest.executor_name).department
        except Exception:
            department = ""
        if reest.labor_costs_plan:
            self.fields['labor_costs_plan'].initial = reest.labor_costs_plan
        elif department == "Субподряд":
            self.fields['labor_costs_plan'].initial = 0.1
        if reest.comment:
            self.fields['comment'].initial = reest.comment
        if reest.answer_remark:
            self.fields['answer_remark'].initial = reest.answer_remark
        if reest.total_importance:
            self.fields['total_importance'].initial = reest.total_importance
        if reest.root_cause_list:
            self.fields['root_cause_list'].initial = reest.root_cause_list
        if reest.root_cause_text:
            self.fields['root_cause_text'].initial = reest.root_cause_text
        if reest.root_cause_comment:
            self.fields['root_cause_comment'].initial = reest.root_cause_comment

    def save_files(self, reestr, name, comment, remark):
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name,
                             comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class GIPform2(forms.ModelForm):
    class Meta:
        model = reestr
        fields = (
        'project_date_contract', 'project_name', 'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date',
        'num_reestr', 'num_remark', 'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name',
        'responsibleTrouble_name',
        'executor_fail_name', 'executor_name', 'answer_date_plan', 'answer_deadline_correct_plan', 'executor_fail_text',
        'labor_costs_plan', 'comment', 'answer_remark', 'total_importance', 'root_cause_list', 'reestrID', 'gip',
        'root_cause_comment', 'root_cause_text', 'status', 'importance1', 'importance2', 'importance3', 'importance4',
        'importance5', 'importance6', 'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment')
        error_messages = {
            'remark_name': {'required': 'Пожалуйста, внесите данные', },
            'rational': {'required': 'Пожалуйста, внесите данные', },
            'designation_name': {'required': 'Пожалуйста, внесите данные', },
            'section_name': {'required': 'Пожалуйста, внесите данные', },
            'responsibleTrouble_name': {'required': 'Пожалуйста, внесите данные', },
            'executor_fail_name': {'required': "Пожалуйста, внесите данные"},
            'executor_name': {'required': "Пожалуйста, внесите данные"},
            'answer_date_plan': {'required': "Пожалуйста, внесите данные"},
            'answer_deadline_correct_plan': {'required': "Пожалуйста, внесите данные"},
            'labor_costs_plan': {'required': "Пожалуйста, внесите данные"},
            'comment': {'required': "Пожалуйста, внесите данные"},
            'answer_remark': {'required': "Пожалуйста, внесите данные"},
            'total_importance': {'required': "Пожалуйста, внесите данные"},
            'root_cause_list': {'required': "Пожалуйста, внесите данные"},
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'rational': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'title': 'Пример: ТХ', 'autocomplete': 'off'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'title': 'Пример: 099-3053-1001624-ТХ', 'autocomplete': 'off'}),

            'answer_date_plan': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'answer_deadline_correct_plan': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'labor_costs_plan': forms.NumberInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'required': 'required', 'step': '0.05',
                       'min': '0.1'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания',
                       'autocomplete': 'off', 'required': 'required'}),
            'answer_remark': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'importance1': forms.RadioSelect(choices=[(True, 'Да'), (False, 'Нет')]),
            'importance2': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance3': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance4': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance5': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance6': forms.RadioSelect(
                choices=[(True, 'Вина/Инициатива Заказчика'), (False, 'Вина проектировщика')]),
            'importance7': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'imp3_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'imp4_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'imp7_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'total_importance': forms.TextInput(
                attrs={'class': 'form-textinput', 'id': 'total_imp', 'autocomplete': 'off', 'required': 'required'}),
            'root_cause_list': forms.TextInput(
                attrs={'class': 'form-textinput', 'id': 'root_cause', 'autocomplete': 'off', 'required': 'required'}),
            'root_cause_text': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'root_cause0', 'hidden': 'hidden'}),
            'root_cause_comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'executor_fail_text',
                       'hidden': 'hidden'})
        }

    responsibleTrouble_name = forms.ModelChoiceField(
        queryset=User.objects.filter((Q(groups=1) | Q(groups=2))).order_by('last_name'),
        empty_label='-----',
        widget=forms.Select(
            attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
        error_messages={'required': 'Пожалуйста, внесите данные'})
    q1 = Q(groups=2) | Q(groups=3) | Q(groups=1)
    q2 = Q(groups=4)
    q3 = Q(username="emptyUSER")
    qs = User.objects.filter(q1 | q2 | q3).annotate(
        search_type_ordering=Case(When(q3, Value(2)), When(q1, then=Value(1)), When(q2, then=Value(0)),
                                  default=Value(-1))).order_by('-search_type_ordering', 'last_name')
    executor_fail_name = forms.ModelChoiceField(queryset=qs,
                                                empty_label='-----', required=False,
                                                widget=forms.Select(
                                                    attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                                error_messages={'required': 'Пожалуйста, внесите данные'})
    qs = User.objects.filter(q1 | q2).annotate(
        search_type_ordering=Case(When(q1, then=Value(1)), When(q2, then=Value(0)), default=Value(-1))).order_by(
        '-search_type_ordering', 'last_name')
    executor_name = forms.ModelChoiceField(queryset=qs,
                                           empty_label='-----',
                                           widget=forms.Select(
                                               attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                           error_messages={'required': 'Пожалуйста, внесите данные'})

    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=False)
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=False)
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=False)
    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reest = reestr.objects.all()
        # reest = reestr.objects.all().last()
        self.fields['status'].initial = reest.status
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['answer_date_plan'].initial = str(reest.answer_date_plan)
        self.fields['answer_deadline_correct_plan'].initial = str(reest.answer_deadline_correct_plan)
        self.fields['labor_costs_plan'].initial = reest.labor_costs_plan
        self.fields['comment'].initial = reest.comment
        self.fields['answer_remark'].initial = reest.answer_remark
        self.fields['total_importance'].initial = reest.total_importance
        self.fields['root_cause_list'].initial = reest.root_cause_list
        self.fields['root_cause_text'].initial = reest.root_cause_text
        self.fields['root_cause_comment'].initial = reest.root_cause_comment
        self.fields['executor_fail_text'].initial = reest.executor_fail_text
        self.fields['reestrID'].initial = reest.reestrID
        self.fields['gip'].initial = reest.gip
        self.fields['importance1'].initial = reest.importance1
        self.fields['importance2'].initial = reest.importance2
        self.fields['importance3'].initial = reest.importance3
        self.fields['importance4'].initial = reest.importance4
        self.fields['importance5'].initial = reest.importance5
        self.fields['importance6'].initial = reest.importance6
        self.fields['importance7'].initial = reest.importance7
        self.fields['imp3_comment'].initial = reest.imp3_comment
        self.fields['imp4_comment'].initial = reest.imp4_comment
        self.fields['imp7_comment'].initial = reest.imp7_comment

        if reest.responsibleTrouble_name:
            self.fields['responsibleTrouble_name'].initial = reest.responsibleTrouble_name
        if reest.executor_fail_name:
            self.fields['executor_fail_name'].initial = reest.executor_fail_name
        if reest.executor_name:
            self.fields['executor_name'].initial = reest.executor_name

    def save_files(self, reestr, name, comment, cause_name, cause_comment, remark):
        # for upload in self.files.getlist("add_files"):
        # add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
        # file_size=getHumanReadable(upload.size),
        # belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/"+remark)
        # add_file.save()
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=cause_name,
                             comment=cause_comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class BossForm2(forms.ModelForm):
    class Meta:
        model = reestr
        fields = (
        'project_date_contract', 'project_name', 'out_mail_num', 'out_mail_date', 'in_mail_num', 'in_mail_date',
        'num_reestr', 'num_remark', 'remark_v', 'remark_name', 'rational', 'designation_name', 'section_name',
        'executor_fail_name', 'executor_name', 'answer_date_plan', 'answer_deadline_correct_plan',
        'labor_costs_plan', 'comment', 'answer_remark', 'total_importance', 'root_cause_list', 'root_cause_text',
        'root_cause_comment', 'responsibleTrouble_name', 'gip', 'reestrID', 'status', 'executor_fail_text',
        'importance1', 'importance2', 'importance3', 'importance4',
        'importance5', 'importance6', 'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment')
        error_messages = {
            'remark_name': {'required': 'Пожалуйста, внесите данные', },
            'rational': {'required': 'Пожалуйста, внесите данные', },
            'designation_name': {'required': 'Пожалуйста, внесите данные', },
            'section_name': {'required': 'Пожалуйста, внесите данные', },
            'responsibleTrouble_name': {'required': 'Пожалуйста, внесите данные', },
            'executor_fail_name': {'required': "Пожалуйста, внесите данные"},
            'executor_name': {'required': "Пожалуйста, внесите данные"},
            'answer_date_plan': {'required': "Пожалуйста, внесите данные"},
            'answer_deadline_correct_plan': {'required': "Пожалуйста, внесите данные"},
            'labor_costs_plan': {'required': "Пожалуйста, внесите данные"},
            'comment': {'required': "Пожалуйста, внесите данные"},
            'answer_remark': {'required': "Пожалуйста, внесите данные"},
            'total_importance': {'required': "Пожалуйста, внесите данные"},
            'root_cause_list': {'required': "Пожалуйста, внесите данные"},
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_reviewer': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'rational': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'title': 'Пример: ТХ', 'readonly': 'readonly'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'title': 'Пример: 099-3053-1001624-ТХ', 'readonly': 'readonly'}),

            'answer_date_plan': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'answer_deadline_correct_plan': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'labor_costs_plan': forms.NumberInput(
                attrs={'class': 'form-textinput', 'step': '0.05', 'min': '0.1', 'autocomplete': 'off',
                       'required': 'required'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания',
                       'autocomplete': 'off', 'required': 'required'}),
            'answer_remark': forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'importance1': forms.RadioSelect(choices=[(True, 'Да'), (False, 'Нет')]),
            'importance2': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance3': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance4': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance5': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'importance6': forms.RadioSelect(
                choices=[(True, 'Вина/Инициатива Заказчика'), (False, 'Вина проектировщика')]),
            'importance7': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')]),
            'imp3_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'imp4_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'imp7_comment': forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
            'total_importance': forms.TextInput(attrs={'class': 'form-textinput',
                                                       'placeholder': '', 'id': 'total_imp', 'autocomplete': 'off',
                                                       'required': 'required'}),
            'root_cause_list': forms.TextInput(
                attrs={'class': 'form-textinput', 'id': 'root_cause', 'autocomplete': 'off', 'required': 'required'}),
            'root_cause_text': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'root_cause0', 'hidden': 'hidden'}),
            'root_cause_comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'executor_fail_text',
                       'hidden': 'hidden'})
        }

    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reest = reestr.objects.all()
        # reest = reestr.objects.all().last()
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['answer_date_plan'].initial = str(reest.answer_date_plan)
        self.fields['answer_deadline_correct_plan'].initial = str(reest.answer_deadline_correct_plan)
        self.fields['labor_costs_plan'].initial = reest.labor_costs_plan
        self.fields['comment'].initial = reest.comment
        self.fields['answer_remark'].initial = reest.answer_remark
        self.fields['total_importance'].initial = reest.total_importance
        self.fields['root_cause_list'].initial = reest.root_cause_list
        self.fields['root_cause_text'].initial = reest.root_cause_text
        self.fields['root_cause_comment'].initial = reest.root_cause_comment
        self.fields['executor_fail_text'].initial = reest.executor_fail_text

        self.fields['responsibleTrouble_name'].initial = reest.responsibleTrouble_name
        self.fields['gip'].initial = reest.gip
        self.fields['reestrID'].initial = reest.reestrID
        self.fields['status'].initial = reest.status
        self.fields['importance1'].initial = reest.importance1
        self.fields['importance2'].initial = reest.importance2
        self.fields['importance3'].initial = reest.importance3
        self.fields['importance4'].initial = reest.importance4
        self.fields['importance5'].initial = reest.importance5
        self.fields['importance6'].initial = reest.importance6
        self.fields['importance7'].initial = reest.importance7
        self.fields['imp3_comment'].initial = reest.imp3_comment
        self.fields['imp4_comment'].initial = reest.imp4_comment
        self.fields['imp7_comment'].initial = reest.imp7_comment

        q1 = (Q(groups=2) | Q(groups=3) | Q(groups=1)) & Q(
            departments__department=reest.responsibleTrouble_name.departments.department)
        q2 = Q(groups=4)
        q3 = Q(username="emptyUSER")
        qs = User.objects.filter(q1 | q2 | q3).annotate(
            search_type_ordering=Case(When(q3, Value(2)), When(q1, then=Value(1)), When(q2, then=Value(0)),
                                      default=Value(-1))).order_by('-search_type_ordering', 'last_name')
        self.fields['executor_fail_name'] = forms.ModelChoiceField(queryset=qs,
                                                                   empty_label='-----', required=False,
                                                                   widget=forms.Select(
                                                                       attrs={'class': 'form-textinput',
                                                                              'autocomplete': 'off'}),
                                                                   error_messages={
                                                                       'required': 'Пожалуйста, внесите данные'})
        qs = User.objects.filter(q1 | q2).annotate(
            search_type_ordering=Case(When(q1, then=Value(1)), When(q2, then=Value(0)), default=Value(-1))).order_by(
            '-search_type_ordering', 'last_name')
        self.fields['executor_name'] = forms.ModelChoiceField(queryset=qs,
                                                              empty_label='-----',
                                                              widget=forms.Select(
                                                                  attrs={'class': 'form-textinput',
                                                                         'autocomplete': 'off'}),
                                                              error_messages={'required': 'Пожалуйста, внесите данные'})

        if reest.executor_fail_name:
            self.fields['executor_fail_name'].initial = reest.executor_fail_name
        if reest.executor_name:
            self.fields['executor_name'].initial = reest.executor_name

    def save_files(self, reestr, name, comment, remark):
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name,
                             comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class FinalForm(forms.ModelForm):
    class Meta:
        model = reestr
        fields = (
        'project_date_contract', 'project_name', 'executor_fail_text', 'out_mail_num', 'out_mail_date', 'in_mail_num',
        'in_mail_date', 'num_reestr', 'num_remark', 'remark_v', 'remark_name', 'rational', 'designation_name',
        'section_name', 'answer_date_plan', 'answer_date_fact', 'answer_deadline_correct_plan',
        'answer_deadline_correct_fact',
        'labor_costs_plan', 'labor_costs_fact', 'comment', 'answer_remark', 'link_tech_name', 'total_importance',
        'root_cause_comment', 'root_cause_list', 'root_cause_text', 'importance1', 'importance2', 'importance3',
        'importance4',
        'importance5', 'importance6', 'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment')
        error_messages = {
            'answer_date_plan': {'required': "Пожалуйста, внесите данные"},
            'answer_deadline_correct_plan': {'required': "Пожалуйста, внесите данные"},
            'labor_costs_plan': {'required': "Пожалуйста, внесите данные"},
            'answer_date_fact': {'required': "Пожалуйста, внесите данные"},
            'answer_deadline_correct_fact': {'required': "Пожалуйста, внесите данные"},
            'labor_costs_fact': {'required': "Пожалуйста, внесите данные"},
            'answer_remark': {'required': "Пожалуйста, внесите данные"},
            'link_tech_name': {'required': "Пожалуйста, внесите данные"},
            'root_cause_list': {'required': "Пожалуйста, внесите данные"},
        }
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'rational': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: ТХ'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'title': 'Пример: 099-3053-1001624-ТХ', 'readonly': 'readonly'}),

            'answer_date_plan': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'answer_date_fact': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'answer_deadline_correct_plan': forms.DateInput(
                attrs={'class': 'form-readonly', 'empty_label': "---", 'readonly': 'readonly'}),
            'answer_deadline_correct_fact': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'labor_costs_plan': forms.NumberInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'labor_costs_fact': forms.NumberInput(
                attrs={'class': 'form-textinput', 'step': '0.05', 'min': '0.1', 'autocomplete': 'off',
                       'required': 'required'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания'}),
            'answer_remark': forms.Textarea(
                attrs={'class': 'form-textinput', 'required': 'required', 'autocomplete': 'off'}),
            'link_tech_name': forms.TextInput(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'required': 'required'}),
            'importance1': forms.RadioSelect(choices=[(True, 'Да'), (False, 'Нет')], attrs={'readonly': 'readonly'}),
            'importance2': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance3': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance4': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance5': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance6': forms.RadioSelect(
                choices=[(True, 'Вина/Инициатива Заказчика'), (False, 'Вина проектировщика')],
                attrs={'readonly': 'readonly'}),
            'importance7': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'imp3_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'imp4_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'imp7_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'total_importance': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly',
                                                       'placeholder': '', 'id': 'total_imp'}),
            'root_cause_list': forms.TextInput(
                attrs={'required': 'required', 'class': 'form-textinput', 'id': 'root_cause'}),
            'root_cause_text': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'root_cause0', 'hidden': 'hidden'}),
            'root_cause_comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-readonly', 'id': 'executor_fail_text', 'readonly': 'readonly',
                       'hidden': 'hidden'})
        }

    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=False)
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=False)
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=False)
    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reest = reestr.objects.all()
        # reest = reestr.objects.all().last()
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['answer_date_plan'].initial = reest.answer_date_plan
        self.fields['answer_deadline_correct_plan'].initial = reest.answer_deadline_correct_plan
        self.fields['labor_costs_plan'].initial = reest.labor_costs_plan
        self.fields['importance1'].initial = reest.importance1
        self.fields['importance2'].initial = reest.importance2
        self.fields['importance3'].initial = reest.importance3
        self.fields['importance4'].initial = reest.importance4
        self.fields['importance5'].initial = reest.importance5
        self.fields['importance6'].initial = reest.importance6
        self.fields['importance7'].initial = reest.importance7
        self.fields['imp3_comment'].initial = reest.imp3_comment
        self.fields['imp4_comment'].initial = reest.imp4_comment
        self.fields['imp7_comment'].initial = reest.imp7_comment
        if reest.answer_date_fact:
            self.fields['answer_date_fact'].initial = str(reest.answer_date_fact)
        if reest.answer_deadline_correct_fact:
            self.fields['answer_deadline_correct_fact'].initial = str(reest.answer_deadline_correct_fact)
        try:
            department = departments.objects.get(user=reest.executor_name).department
        except Exception:
            department = ""
        if reest.labor_costs_fact:
            self.fields['labor_costs_fact'].initial = reest.labor_costs_fact
        elif department == "Субподряд":
            self.fields['labor_costs_fact'].initial = 0.1
        self.fields['comment'].initial = reest.comment
        self.fields['answer_remark'].initial = reest.answer_remark
        self.fields['total_importance'].initial = reest.total_importance
        self.fields['root_cause_list'].initial = reest.root_cause_list
        if reest.link_tech_name and reest.link_tech_name != "":
            self.fields['link_tech_name'].initial = reest.link_tech_name
        if reest.root_cause_text and reest.root_cause_text != "":
            self.fields['root_cause_text'].initial = reest.root_cause_text
        if reest.root_cause_comment and reest.root_cause_comment != "":
            self.fields['root_cause_comment'].initial = reest.root_cause_comment
        if reest.executor_fail_text and reest.executor_fail_text != "":
            self.fields['executor_fail_text'].initial = reest.executor_fail_text

    def save_files(self, reestr, name, comment, remark):
        for upload in self.files.getlist("add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name,
                             comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()


class CloseForm(forms.ModelForm):
    class Meta:
        model = reestr
        fields = ('cancel_remark', 'cancel_remark_date')
        error_messages = {
            'cancel_remark': {'required': "Пожалуйста, внесите данные"},
            'cancel_remark_date': {'required': "Пожалуйста, внесите данные"}
        }
        widgets = {
            'cancel_remark': forms.Textarea(attrs={'class': 'form-textinput', 'required': 'required'}),
            'cancel_remark_date': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year) + '-12-31'}),
        }

    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    closed_remarks = forms.CharField(widget=forms.TextInput(attrs={'hidden': 'hidden', 'id': 'forClose'}),
                                     required=False)

    def save_files(self, reestr, name, comment):
        for upload in self.files.getlist("add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr)
            add_file.save()


class ReturnForm(forms.Form):
    date_field = forms.DateField(widget=AdminDateWidget(
        attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
               'max': str(date.today().year) + '-12-31'}),
                                 required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}),
                                required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    file_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    file_comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off'}),
                                   required=True, error_messages={'required': "Пожалуйста, внесите данные"})
    returned_remarks = forms.CharField(widget=forms.TextInput(attrs={'hidden': 'hidden', 'id': 'forClose'}),
                                       required=False)

    def save_files(self, reestr, name, comment, dateValue):
        for upload in self.files.getlist("add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=dateValue, file_name=name, comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr)
            add_file.save()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = reestr
        fields = ('gip', 'num_reestr', 'num_remark', 'remark_name',)


class AnswerForm(forms.ModelForm):
    class Meta:
        model = reestr
        fields = (
        'project_date_contract', 'project_name', 'executor_fail_text', 'out_mail_num', 'out_mail_date', 'in_mail_num',
        'in_mail_date', 'num_reestr', 'num_remark', 'remark_v', 'remark_name', 'rational', 'designation_name',
        'section_name', 'answer_date_plan', 'answer_date_fact', 'answer_deadline_correct_plan',
        'answer_deadline_correct_fact',
        'labor_costs_plan', 'labor_costs_fact', 'comment', 'answer_remark', 'link_tech_name', 'total_importance',
        'root_cause_list',
        'root_cause_comment', 'root_cause_text', 'status', 'importance1', 'importance2', 'importance3', 'importance4',
        'importance5', 'importance6', 'importance7', 'imp3_comment', 'imp4_comment', 'imp7_comment')
        widgets = {
            'project_date_contract': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'project_name': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'out_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_num': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'in_mail_date': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_reestr': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'num_remark': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'remark_v': forms.NumberInput(attrs={'class': 'form-readonly', 'id': 'remark_v', 'readonly': 'readonly'}),
            'remark_name': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'rational': forms.Textarea(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'designation_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'title': 'Пример: ТХ'}),
            'section_name': forms.TextInput(
                attrs={'class': 'form-readonly', 'title': 'Пример: 099-3053-1001624-ТХ', 'readonly': 'readonly'}),

            'answer_date_plan': forms.DateInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'answer_date_fact': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'answer_deadline_correct_plan': forms.DateInput(
                attrs={'class': 'form-readonly', 'empty_label': "---", 'readonly': 'readonly'}),
            'answer_deadline_correct_fact': AdminDateWidget(
                attrs={'class': 'form-dateinput', 'required': 'required', 'type': 'date', 'min': '2000-01-01',
                       'max': str(date.today().year + 1) + '-12-31'}),
            'labor_costs_plan': forms.NumberInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'labor_costs_fact': forms.NumberInput(
                attrs={'class': 'form-textinput', 'step': '0.05', 'min': '0.1', 'autocomplete': 'off',
                       'required': 'required'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'title': 'Указывается информация о статусе замечания'}),
            'answer_remark': forms.Textarea(attrs={'class': 'form-textinput', 'required': 'required'}),
            'link_tech_name': forms.TextInput(attrs={'class': 'form-textinput'}),
            'importance1': forms.RadioSelect(choices=[(True, 'Да'), (False, 'Нет')], attrs={'readonly': 'readonly'}),
            'importance2': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance3': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance4': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance5': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'importance6': forms.RadioSelect(
                choices=[(True, 'Вина/Инициатива Заказчика'), (False, 'Вина проектировщика')],
                attrs={'readonly': 'readonly'}),
            'importance7': forms.RadioSelect(choices=[(True, 'Требуется'), (False, 'Не требуется')],
                                             attrs={'readonly': 'readonly'}),
            'imp3_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'imp4_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'imp7_comment': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly'}),
            'total_importance': forms.TextInput(attrs={'class': 'form-readonly', 'readonly': 'readonly',
                                                       'placeholder': '', 'id': 'total_imp'}),
            'root_cause_list': forms.TextInput(
                attrs={'required': 'required', 'class': 'form-textinput', 'id': 'root_cause'}),
            'root_cause_text': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'id': 'root_cause0', 'hidden': 'hidden'}),
            'root_cause_comment': forms.Textarea(
                attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
            'executor_fail_text': forms.TextInput(
                attrs={'class': 'form-readonly', 'readonly': 'readonly', 'id': 'executor_fail_text'})
        }

    cause_add_files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True, 'hidden': 'hidden'}),
                                      required=False)
    cause_file_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)
    cause_file_comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textinput', 'autocomplete': 'off', 'hidden': 'hidden'}),
        required=False)

    def __init__(self, reest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project_date_contract'].initial = reest.project_date_contract
        self.fields['project_name'].initial = reest.project_name
        self.fields['out_mail_num'].initial = reest.out_mail_num
        self.fields['out_mail_date'].initial = reest.out_mail_date
        self.fields['in_mail_num'].initial = reest.in_mail_num
        self.fields['in_mail_date'].initial = reest.in_mail_date
        self.fields['num_reestr'].initial = reest.num_reestr
        self.fields['num_remark'].initial = reest.num_remark
        self.fields['remark_v'].initial = reest.remark_v
        self.fields['remark_name'].initial = reest.remark_name
        self.fields['rational'].initial = reest.rational
        self.fields['designation_name'].initial = reest.designation_name
        self.fields['section_name'].initial = reest.section_name
        self.fields['answer_date_plan'].initial = reest.answer_date_plan
        self.fields['answer_deadline_correct_plan'].initial = reest.answer_deadline_correct_plan
        self.fields['labor_costs_plan'].initial = reest.labor_costs_plan
        self.fields['answer_date_fact'].initial = str(reest.answer_date_fact)
        self.fields['answer_deadline_correct_fact'].initial = str(reest.answer_deadline_correct_fact)
        self.fields['labor_costs_fact'].initial = reest.labor_costs_fact
        self.fields['comment'].initial = reest.comment
        self.fields['answer_remark'].initial = reest.answer_remark
        self.fields['link_tech_name'].initial = reest.link_tech_name
        self.fields['total_importance'].initial = reest.total_importance
        self.fields['root_cause_list'].initial = reest.root_cause_list
        self.fields['root_cause_text'].initial = reest.root_cause_text
        self.fields['root_cause_comment'].initial = reest.root_cause_comment
        self.fields['executor_fail_text'].initial = reest.executor_fail_text
        self.fields['status'].initial = reest.status
        self.fields['importance1'].initial = reest.importance1
        self.fields['importance2'].initial = reest.importance2
        self.fields['importance3'].initial = reest.importance3
        self.fields['importance4'].initial = reest.importance4
        self.fields['importance5'].initial = reest.importance5
        self.fields['importance6'].initial = reest.importance6
        self.fields['importance7'].initial = reest.importance7
        self.fields['imp3_comment'].initial = reest.imp3_comment
        self.fields['imp4_comment'].initial = reest.imp4_comment
        self.fields['imp7_comment'].initial = reest.imp7_comment
    def save_files(self, reestr, name, comment, remark):
        for upload in self.files.getlist("cause_add_files"):
            add_file = files(reestr=reestr, file=upload, upload_date=date.today(), file_name=name,
                             comment=comment,
                             file_size=getHumanReadable(upload.size),
                             belong_to=reestr.project_dogovor.number[4:9] + reestr.num_reestr + "/" + remark)
            add_file.save()

# class DashboardForm(forms.Form):
# years = forms.ChoiceField(choices=CHOICES_YEARS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-Year"}))
# gips = forms.ChoiceField(choices=CHOICES_GIPS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-GIP"}))
# reviewers = forms.ChoiceField(choices=CHOICES_REVIEWERS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-reviewer"}))
# customers = forms.ChoiceField(choices=CHOICES_CUSTOMERS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-customers"}))
# contracts = forms.ChoiceField(choices=CHOICES_CONTRACTS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-contracts"}))
# reestrs = forms.ChoiceField(choices=CHOICES_REESTRS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-reestrs"}))
# importances = forms.ChoiceField(choices=CHOICES_IMPORTANCE, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-importance"}))
# respons = forms.ChoiceField(choices=CHOICES_RESPONS, initial="н", widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-respons"}))
# departments = forms.ChoiceField(choices=CHOICES_DEPARTMENTS, widget=forms.Select(attrs={"multiple": "multiple", "class": "form-dashboard", "id": "var-departments"}))