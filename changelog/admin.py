from django.contrib import admin
from changelog.models import ChangeLog
from django.contrib.admin import DateFieldListFilter

class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('changed', 'user', 'action_on_model', 'model', 'record_id')
    readonly_fields = ('user', )
    list_filter = ('model', 'action_on_model', 'changed')
    search_fields = ('changed', 'record_id', 'user__last_name')

admin.site.register(ChangeLog, ChangeLogAdmin)