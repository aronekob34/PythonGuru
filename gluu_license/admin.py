from django.contrib import admin

from gluu_license import models


class LicenseRecordAdmin(admin.ModelAdmin):

    model = models.LicenseRecord
    list_display = ('year', 'month', 'license', 'number_licenses', 'details')
    readonly_fields = ('created',)

admin.site.register(models.LicenseRecord, LicenseRecordAdmin)


class LicenseAdmin(admin.ModelAdmin):

    model = models.License
    list_display = ('id', 'license_id', 'account')
    readonly_fields = ('creation_date',)

admin.site.register(models.License, LicenseAdmin)
