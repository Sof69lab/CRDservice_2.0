from django.db import models

class ChangeloggableMixin(models.Model):
    """Значения полей сразу после инициализации объекта"""
    _original_values = None
    _name_dict = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(ChangeloggableMixin, self).__init__(*args, **kwargs)

        # self._original_values = {
        #     field.name: getattr(self, field.name)
        #     for field in self._meta.fields if field.name not in ['added', 'changed'] and hasattr(self, field.name)
        # }
        self._original_values = {}
        self._name_dict = {}
        for field in self._meta.fields:
            if type(field) == models.fields.related.ForeignKey:
                self._original_values[field.verbose_name] = (getattr(self, f'{field.name}_id'))
            else:
                self._original_values[field.verbose_name] = getattr(self, field.name)
            self._name_dict[field.verbose_name] = field.name


    def get_changed_fields(self):
        """
        Получаем измененные данные
        """
        result = {}
        for name, value in self._original_values.items():
            if value != getattr(self, self._name_dict[name]):
                temp = {}
                if value and value != "":
                    temp['old_' + name] = value
                temp[name] = getattr(self, self._name_dict[name])
                # Дополнительная проверка для полей Foreign Key
                if self._meta.get_field(self._name_dict[name]).get_internal_type() == ('ForeignKey'):
                    if value != getattr(self, f'{self._name_dict[name]}_id'):
                        result.update(temp)
                else:
                    result.update(temp)
        return result

    def get_all_fields(self):
        result = {}
        for name, value in self._name_dict.items():
            temp = {}
            temp[name] = getattr(self, self._name_dict[name])
            result.update(temp)
        return result