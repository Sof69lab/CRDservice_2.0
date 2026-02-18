from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_delete, post_save
from changelog.mixins import ChangeloggableMixin
from changelog.signals import journal_save_handler, journal_delete_handler

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/...
    print(instance.belong_to)
    if "/" in instance.belong_to:
        i = 0
        while instance.belong_to[i] != "/":
            i += 1
        print(instance.belong_to[i+1:])
        return 'реестр_{0}/{1}/{2}'.format(instance.reestr.project_dogovor.number[4:9]+instance.reestr.num_reestr, instance.belong_to[i+1:], filename)
    else:
        return 'реестр_{0}/{1}'.format(instance.reestr.project_dogovor.number[4:9]+instance.reestr.num_reestr, filename)

def get_full_name(self):
    return self.last_name + ' ' + self.first_name

User.add_to_class("__str__", get_full_name)

form = "Формирование"
write = "На заполнении"
writeGIP = "На заполнении ГИПом"
writeBoss = "На заполнении руководителем"
writeEmployee = "На заполнении исполнителем"
approvingBoss = "На согласовании руководителем"
approvingGIP = "На согласовании ГИПом"
approving = "На согласовании"
rewrite = "На доработке"
rewriteGIP = "На доработке ГИПом"
rewriteBoss = "На доработке руководителем"
rewriteEmployee = "На доработке исполнителем"
approved = "Согласовано ГИПом"
answering = "Подготовка ответов"
answeringGIP = "Подготовка ответов ГИПом"
answeringBoss = "Подготовка ответов руководителем"
answeringEmployee = "Подготовка ответов исполнителем"
ready = "Принято ГИПом"
review = "На согласовании Рецензентом"
final = "Замечание снято"
close = "Закрыт"
hidden = "Скрыт"
STATUS_CHOICES = [
    (form, "Формирование"),
    (write, "На заполнении"),
    (writeGIP, "На заполнении ГИПом"),
    (writeBoss, "На заполнении руководителем"),
    (writeEmployee, "На заполнении исполнителем"),
    (approvingBoss, "На согласовании руководителем"),
    (approvingGIP, "На согласовании ГИПом"),
    (approving, "На согласовании"),
    (rewrite, "На доработке"),
    (rewriteGIP, "На доработке ГИПом"),
    (rewriteBoss, "На доработке руководителем"),
    (rewriteEmployee, "На доработке исполнителем"),
    (approved, "Согласовано ГИПом"),
    (answering, "Подготовка ответов"),
    (answeringGIP, "Подготовка ответов ГИПом"),
    (answeringBoss, "Подготовка ответов руководителем"),
    (answeringEmployee, "Подготовка ответов исполнителем"),
    (ready, "Принято ГИПом"),
    (review, "На согласовании Рецензентом"),
    (final, "Замечание снято"),
    (close, "Закрыт"),
    (hidden, "Скрыт"),
]

direkciya = "Дирекция"
uniid = "УНиИД"
ag = "АГ"
nil5 = "НИЛ-5"
nil11 = "НИЛ-11"
nio28 = "НИО-28"
nil25 = "НИЛ-25"
nil34 = "НИЛ-34"
niokps = "НИО КПС"
fhg = "Гр. ФХГ"
nil31 = "НИЛ-31"
io = "Гр. ИО"
nio33 = "НИО-33"
nil37 = "НИЛ-37"
nil35 = "НИЛ-35"
hal = "ХАЛ"
iso = "ИСО"
hgl = "ХГЛ"
ugi = "УГИ"
oso = "ОСО"
okivd = "ОКиВД"
oeirb = "ОЭиРБ"
eo = "ЭО"
gto = "ГТО"
osss = "ОССС"
otvs = "ОТВС"
so = "СО"
ogit = "ОГиТ"
go = "ГО"
po = "ПО"
oea = "ОЭА"
tho = "ТХО"
ogip = "ОГИП"
crci = "ЦРЦИ"
orim = "ОРИМ"
uprirp = "УПРиРП"
opr = "ОПР"
osukil = "ОСУКиЛ"
igi = "Гр. ИГИ"
igdi = "Гр. ИГДИ"
iei = "Гр. ИЭИ"
igmi = "Гр. ИГМИ"
igfi = "Гр.ИГФИ"
sub = "Субподряд"
DEPARTMENT_CHOICES = [
    (direkciya, "Дирекция"),
    (uniid, "Управление по научной и инновационной деятельности ("+uniid+")"),
    (ag, "Аналитическая группа ("+ag+")"),
    (nil5, "Комплексная научно-исследовательская лаборатория глубинного захоронения жидких радиоактивных и промышленных отходов ("+nil5+")"),
    (nil11, "Научно-исследовательская лаборатория радиационной безопасности ("+nil11+")"),
    (nio28, "Научно-исследовательский отдел горных работ ("+nio28+")"),
    (nil25, "Научно-исследовательская лаборатория горнотехнического моделирования ("+nil25+")"),
    (nil34, "Научно-исследовательская лаборатория совершенствования горно- технологических процессов добычи ("+nil34+")"),
    (niokps, "Научно-исследовательский отдел комплексной переработки сырья ("+niokps+")"),
    (fhg, "Группа физико-химической геотехнологии ("+fhg+")"),
    (nil31, "Научно-исследовательская лаборатория гидрометаллургических технологий ("+nil31+")"),
    (io, "Группа ионного обмена ("+io+")"),
    (nio33, "Научно-исследовательский отдел технологий, геомеханики и недропользования ("+nio33+")"),
    (nil37, "Научно-исследовательская лаборатория геомеханики и недропользования ("+nil37+")"),
    (nil35, "Научно-исследовательская лаборатория технологии выщелачивания ("+nil35+")"),
    (hal, "Химико-аналитическая лаборатория ("+hal+")"),
    (iso, "Инженерно-строительный отдел ("+iso+")"),
    (hgl, "Химико-грунтоведческая лаборатория ("+hgl+")"),
    (ugi, "Управление главного инженера ("+ugi+")"),
    (oso, "Общестроительный отдел ("+oso+")"),
    (okivd, "Отдел комплектации и выпуска документации ("+okivd+")"),
    (oeirb, "Отдел экологии и радиационной безопасности ("+oeirb+")"),
    (eo, "Электротехнический отдел ("+eo+")"),
    (gto, "Гидротехнический отдел ("+gto+")"),
    (osss, "Отдел связи, сигнализации и спецразделов ("+osss+")"),
    (otvs, "Отдел тепловодоснабжения ("+otvs+")"),
    (so, "Сметный отдел ("+so+")"),
    (ogit, "Отдел генплана и транспорта ("+ogit+")"),
    (go, "Горный отдел ("+go+")"),
    (po, "Производственный отдел ("+po+")"),
    (oea, "Отдел экономического анализа ("+oea+")"),
    (tho, "Технологический отдел ("+tho+")"),
    (ogip, "Отдел главных инженеров проекта ("+ogip+")"),
    (crci, "Центр развития цифрового инжиниринга ("+crci+")"),
    (orim, "Отдел развития информационного моделирования ("+orim+")"),
    (uprirp, "Управление перспективного развития и реализации проектов ("+uprirp+")"),
    (opr, "Отдел перспективного развития ("+opr+")"),
    (osukil, "Отдел стандартизации, управления качеством и лицензирования ("+osukil+")"),
    (igi, "Группа инженерно-геологических изыскани ("+igi+")"),
    (igdi, "Группа инженерно-геодезических изысканий ("+igdi+")"),
    (iei, "Группа инженерно-экологических изысканий ("+iei+")"),
    (igmi, "Группа инженерно-гидрометеорологических изысканий ("+igmi+")"),
    (igfi, "Группа инженерно-геофизических исследований ("+igfi+")"),
    (sub, "Субподряд"),
]

class departments(models.Model):
    class Meta:
        verbose_name = "принадлежность"
        verbose_name_plural = "Штатная расстановка"
    user = models.OneToOneField(User, verbose_name="Сотрудник", on_delete=models.CASCADE)
    department = models.TextField(verbose_name="Наименование структурного подразделения (отдела, службы,бюро,участка, группы)", choices=DEPARTMENT_CHOICES)
    substitute = models.ManyToManyField(User, related_name="subs", verbose_name="Замещает", blank=True)
    def __str__(self):
        return f"{self.user}"

class customers(models.Model):
    class Meta:
        verbose_name = "заказчик"
        verbose_name_plural = "Заказчики"
    name = models.TextField(verbose_name="Наименование краткое")
    def __str__(self):
        return f"{self.name}"

class reviewers(models.Model):
    class Meta:
        verbose_name = "рецензент"
        verbose_name_plural = "Рецензенты"
    name = models.TextField(verbose_name="Наименование")
    def __str__(self):
        return f"{self.name}"

class contracts(models.Model):
    class Meta:
        verbose_name = "договор"
        verbose_name_plural = "Договоры"
    customer = models.ForeignKey(customers, on_delete=models.CASCADE, verbose_name="Заказчик")
    number = models.TextField(verbose_name="№ договора")
    name = models.TextField(verbose_name="Наименование договора")
    date = models.DateField(verbose_name="Дата договора")
    num_reestrs = models.IntegerField(verbose_name="Общее число реестров", default=0)
    def __str__(self):
        return f"{self.number}"

class reestInfo(ChangeloggableMixin, models.Model):
    class Meta:
        verbose_name = "реестр"
        verbose_name_plural = "Реестры"
    reestr_index = models.TextField(verbose_name="Идентификатор", blank=True, null=True)
    #заголовок
    customer = models.ForeignKey(customers, on_delete=models.CASCADE, verbose_name="Заказчик")
    project_dogovor = models.ForeignKey(contracts, on_delete=models.CASCADE, verbose_name="Договор №")
    project_date_contract = models.DateField(verbose_name="Дата договора")
    project_name = models.TextField(verbose_name="Наименование договора")
    gip = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ГИП", related_name='gip_set1')
    project_reviewer = models.ForeignKey(reviewers, on_delete=models.CASCADE, verbose_name="Рецензент")
    out_mail_num = models.TextField(verbose_name="Письмо исх. №")
    out_mail_date = models.DateField(verbose_name="Письмо исх. дата")
    in_mail_num = models.TextField(verbose_name="Письмо вх. №")
    in_mail_date = models.DateField(verbose_name="Письмо вх. дата")
    # таблица
    num_reestr = models.TextField(verbose_name="Реестр №")
    # другое
    start_date = models.DateField(verbose_name="Дата создания")
    end_date = models.DateField(verbose_name="Срок")
    status = models.TextField(verbose_name="Статус", default="Формирование", choices=STATUS_CHOICES)
    def __str__(self):
        return f"{self.project_dogovor.number[4:8]}-{self.num_reestr}"

post_save.connect(journal_save_handler, sender=reestInfo)
post_delete.connect(journal_delete_handler, sender=reestInfo)

class reestr(ChangeloggableMixin, models.Model):
    class Meta:
        verbose_name = "замечание"
        verbose_name_plural = "Замечания"
    remark_index = models.TextField(verbose_name="Идентификатор", blank=True, null=True)
    reestrID = models.ForeignKey(reestInfo, on_delete=models.CASCADE, verbose_name="ID реестра")
    actuality = models.BooleanField(verbose_name="Актуальность", default=True)
    status = models.TextField(verbose_name="Статус", default="Формирование", choices=STATUS_CHOICES)
    deadline = models.DateField(verbose_name="Срок исполнения текущего статуса", default=timezone.now)
    #ГИП. Формирование реестра
    # заголовок
    customer = models.ForeignKey(customers, on_delete=models.CASCADE, verbose_name="Заказчик")
    project_dogovor = models.ForeignKey(contracts, on_delete=models.CASCADE, verbose_name="Договор №")
    project_date_contract = models.DateField(verbose_name="Дата договора", blank=True)
    project_name = models.TextField(verbose_name="Наименование договора")
    gip = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ГИП", related_name='gip_set')
    project_reviewer = models.ForeignKey(reviewers, on_delete=models.CASCADE, verbose_name="Рецензент")
    out_mail_num = models.TextField(verbose_name="Письмо исх. №")
    out_mail_date = models.DateField(verbose_name="Письмо исх. дата", blank=True)
    in_mail_num = models.TextField(verbose_name="Письмо вх. №")
    in_mail_date = models.DateField(verbose_name="Письмо вх. дата", blank=True)
    # таблица
    num_reestr = models.TextField(verbose_name="Реестр №")
    num_remark = models.TextField(verbose_name="1.1. № Замечания")
    remark_v = models.IntegerField(verbose_name="1.2. Версия замечания") #версия замечания
    remark_name = models.TextField(verbose_name="2. Наименование замечания")
    rational = models.TextField(verbose_name="2.1. Обоснование")
    designation_name = models.TextField(verbose_name="3. Обозначение раздела в проекте")
    section_name = models.TextField(verbose_name="4. Наименование раздела")
    responsibleTrouble_name = models.ForeignKey(User, on_delete=models.CASCADE,
                                                verbose_name="5. Ответственный за устранение замечаний (начальник подразделения)",
                                                related_name='responsTroble_set', blank=True, null=True)
    department = models.TextField(verbose_name="Наименование структурного подразделения (отдела, службы,бюро,участка, группы)", choices=DEPARTMENT_CHOICES, blank=True, null=True)
    #НП. Заполнение реестра
    executor_fail_name = models.ForeignKey(User, on_delete=models.CASCADE,
                                           verbose_name="6. Исполнитель, допустивший замечание", related_name='executFail_set', blank=True, null=True)
    executor_fail_text = models.TextField(verbose_name="ФИО исполнителя", blank=True, null=True)  # необязательное поле
    executor_name = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="6.1. Исполнитель, ответственный за устранение замечания",
                                      related_name='execut_set', blank=True, null=True)
    answer_date_plan = models.DateField(verbose_name="7. Дата предоставления ответов на замечания (План)", blank=True, null=True)
    answer_deadline_correct_plan = models.DateField(verbose_name="9. Срок внесения корректировок (План)", blank=True, null=True)
    labor_costs_plan = models.FloatField(verbose_name="10.1 Трудозатраты, дн. (на устранение замечания) (План)", blank=True, null=True)
    comment = models.TextField(verbose_name="10.3. Комментарии", blank=True, null=True)
    answer_remark = models.TextField(verbose_name="11. Ответы на замечания", blank=True, null=True)
    importance1 = models.BooleanField(verbose_name="Нарушены требования ЗНП и (или) обязательные требования нормативных документов", blank=True, null=True, default=None)
    importance2 = models.BooleanField(verbose_name="Требуется корректировка документации (свой раздел, глава, том, книга, др. док.)", blank=True, null=True, default=None)
    importance3 = models.BooleanField(verbose_name="Требуется корректировка смежных разделов (глав, томов, др. док.)", blank=True, null=True, default=None)
    imp3_comment = models.TextField(verbose_name="Укажите разделы (главы, тома, др. док.)", blank=True, null=True)
    importance4 = models.BooleanField(verbose_name="Требуется выдача задания смежным подразделениям (без учёта ОКиВД) и (или) получение исходных данных от них", blank=True, null=True, default=None)
    imp4_comment = models.TextField(verbose_name="Укажите подразделения", blank=True, null=True)
    importance5 = models.BooleanField(verbose_name="Требуется корректировка принятых проектных решений", blank=True, null=True, default=None)
    importance6 = models.BooleanField(verbose_name="Корректировка принятых проектных решений требуется по вине/инициативе Заказчика", blank=True, null=True, default=None)
    importance7 = models.BooleanField(verbose_name="Требуется получение дополнительных исходных данных от Заказчика", blank=True, null=True, default=None)
    imp7_comment = models.TextField(verbose_name="Укажите, какие исходные данные требуются от Заказчика", blank=True, null=True)
    total_importance = models.TextField(verbose_name="14. Значимость замечания", blank=True, null=True)
    root_cause_list = models.TextField(verbose_name="15. Коренная причина", blank=True, null=True)
    root_cause_text = models.TextField(verbose_name="Формулировка коренной причины", blank=True, null=True) #необязательное поле
    root_cause_comment = models.TextField(verbose_name="Комментарий к коренной причине", blank=True, null=True)  # необязательное поле
    # подготовка и отправка электронного письма
    #####################################################
    link_tech_name = models.TextField(verbose_name="12. Ссылка  в  технической документации", blank=True, null=True)
    cancel_remark = models.TextField(verbose_name="13. Отметка о снятии замечания", blank=True, null=True)
    cancel_remark_date = models.DateField(verbose_name="Дата", blank=True, null=True)
    answer_date_fact = models.DateField(verbose_name="8. Дата предоставления ответов на замечания (Факт)", blank=True, null=True)
    answer_deadline_correct_fact = models.DateField(verbose_name="10. Срок внесения корректировок (Факт)", blank=True, null=True)
    labor_costs_fact = models.FloatField(verbose_name="10.2. Трудозатраты, дн. (на устранение замечания) (Факт)", blank=True, null=True)
    def __str__(self):
        return f"{self.project_dogovor.number[4:8]}-{self.num_reestr}-{self.num_remark}-{self.remark_v}"

post_save.connect(journal_save_handler, sender=reestr)
post_delete.connect(journal_delete_handler, sender=reestr)

class files(ChangeloggableMixin, models.Model):
    class Meta:
        verbose_name = "файл"
        verbose_name_plural = "Файлы"
    reestr = models.ForeignKey(reestInfo, on_delete=models.CASCADE, verbose_name="ID реестра")
    belong_to = models.TextField(blank=True, null=True, verbose_name="Принадлежность")
    file = models.FileField(upload_to=user_directory_path, blank=True, null=True, verbose_name="Файл (общий объём загружаемых файлов не должен превышать 30 МБ)")
    file_name = models.TextField(blank=True, null=True, verbose_name="Наименование документа")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    file_size = models.TextField(blank=True, null=True, verbose_name="Размер файла")
    upload_date = models.DateField(verbose_name="Дата загрузки")
    def __str__(self):
        return f"{self.file}"

post_save.connect(journal_save_handler, sender=files)
post_delete.connect(journal_delete_handler, sender=files)

class aiChatSession(models.Model):
    class Meta:
        verbose_name = "сессия"
        verbose_name_plural = "Сессии в чат-боте"
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name = "Пользователь")
    session_key = models.CharField(max_length=100, unique=True, verbose_name = "Сессия")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = "Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name = "Последнее изменение")
    context = models.JSONField(default=dict, verbose_name = "Контекст диалога") # контекст диалога
    def __str__(self):
        return f"{self.session_key}"

class aiChatMessage(models.Model):
    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "Сообщения в чат-боте"
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент'),
        ('system', 'Система')
    ]
    session = models.ForeignKey(aiChatSession, on_delete=models.CASCADE, verbose_name = "Ключ")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name = "Роль")
    content = models.TextField(verbose_name = "Текст")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name = "Время создания")
    metadata = models.JSONField(default=dict, verbose_name = "Метаданные") # для дополнительных данных модели
