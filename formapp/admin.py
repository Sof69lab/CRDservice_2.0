from django.contrib import admin
from formapp.models import reestr, reestInfo, files, contracts, customers, reviewers, departments, aiChatSession, aiChatMessage
from django.contrib.admin.widgets import FilteredSelectMultiple
class reestrAdmin(admin.ModelAdmin):
    search_fields = ('num_reestr', 'num_remark', 'remark_v', 'project_dogovor__number')
    list_filter = ('reestrID', 'project_dogovor')
class reestInfoAdmin(admin.ModelAdmin):
    search_fields = ('num_reestr',)
    list_filter = ('project_dogovor', 'customer', 'project_reviewer',)
class contractsAdmin(admin.ModelAdmin):
    search_fields = ('number',)
    list_filter = ('customer',)
class customersAdmin(admin.ModelAdmin):
    search_fields = ('name',)
class filesAdmin(admin.ModelAdmin):
    search_fields = ('file',)
    list_filter = ('reestr', )
class reviewersAdmin(admin.ModelAdmin):
    search_fields = ('name',)
class departmentsAdmin(admin.ModelAdmin):
    search_fields = ('user__last_name',)
    list_filter = ('department',)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['substitute'].widget = FilteredSelectMultiple(is_stacked=False, verbose_name='Замещает')
        return form
class aiChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'user', 'created_at', 'updated_at')
class aiChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content', 'timestamp')

admin.site.register(reestr, reestrAdmin)
admin.site.register(reestInfo, reestInfoAdmin)
admin.site.register(files, filesAdmin)
admin.site.register(customers, customersAdmin)
admin.site.register(contracts, contractsAdmin)
admin.site.register(reviewers, reviewersAdmin)
admin.site.register(departments, departmentsAdmin)
admin.site.register(aiChatSession, aiChatSessionAdmin)
admin.site.register(aiChatMessage, aiChatMessageAdmin)