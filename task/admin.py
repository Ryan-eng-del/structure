from django.contrib import admin
from . import models
# Register your models here.

class AlgorithmProcessQueueInline(admin.StackedInline):
    model = models.AlgorithmProcessQueue
    extra = 0

class AlgorithmTaskAdmin(admin.ModelAdmin):
    inlines = [AlgorithmProcessQueueInline]


admin.site.register(models.AlgorithmSystemRuntimeControl)
admin.site.register(models.AlgorithmSystemRuntimeStatus)
admin.site.register(models.AlgorithmUserRuntimeStatus)
admin.site.register(models.AlgorithmTask, AlgorithmTaskAdmin)