from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

ACTION_CREATE = 'создал(а)'
ACTION_UPDATE = 'изменил(а)'
ACTION_DELETE = 'удалил(а)'


class ChangeLog(models.Model):
    TYPE_ACTION_ON_MODEL = (
        (ACTION_CREATE, _('Создание')),
        (ACTION_UPDATE, _('Изменение')),
        (ACTION_DELETE, _('Удаление')),
    )
    changed = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата/время изменения')
    model = models.CharField(max_length=255, verbose_name=u'Таблица', null=True)
    record_id = models.CharField(max_length=255, verbose_name=u'Объект', null=True)
    object_id = models.IntegerField(verbose_name="ID объекта")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=u'Автор изменения',
        on_delete=models.CASCADE, null=True)
    action_on_model = models.CharField(
        choices=TYPE_ACTION_ON_MODEL, max_length=50, verbose_name=u'Действие', null=True)
    data = models.JSONField(verbose_name=u'Изменяемые данные модели', default=dict)
    ipaddress = models.CharField(max_length=15, verbose_name=u'IP адресс', null=True)

    class Meta:
        ordering = ('-changed',)
        verbose_name = _('действие пользователя')
        verbose_name_plural = _('Действия пользователей')

    def __str__(self):
        object = ""
        if self.model == "Замечания":
            object = "замечание"
        if self.model == "Реестры":
            object = "реестр"
        if self.model == "Файлы":
            object = "файл"
        return f'{self.user} {self.action_on_model} {object} {self.record_id}'

    @classmethod
    def add(cls, instance, user, ipaddress, action_on_model, data, id=None):
        """Создание записи в журнале регистрации изменений"""
        log = ChangeLog.objects.get(id=id) if id else ChangeLog()
        log.model = instance.__class__._meta.verbose_name_plural
        # log.record_id = instance.pk
        if log.model == "Замечания":
            log.record_id = str(instance.project_dogovor.number[4:8])+'-'+str(instance.num_reestr)+'/'+str(instance.num_remark)+'/'+str(instance.remark_v)
        if log.model == "Реестры":
            log.record_id = str(instance.project_dogovor.number[4:8]) + '-' + str(instance.num_reestr)
        if log.model == "Файлы":
            log.record_id = str(instance.file)
        if user:
            log.user = user
        log.ipaddress = ipaddress
        log.action_on_model = action_on_model
        log.data = data
        log.object_id = instance.id
        log.save()
        return log.pk
