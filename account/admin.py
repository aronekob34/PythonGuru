from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from account import models
from account.forms import PremiumInvitationAdminForm

from account.utils import send_premium_invitation, generate_activation_key

from gluu_license.connectors.license_interface import sync_usage_records


class AccountAdmin(admin.ModelAdmin):

    def sync_license_records(modeladmin, request, queryset):
        for obj in queryset:
            sync_usage_records(obj.license)
    sync_license_records.short_description = 'Get latest license records for license.gluu.org'

    def cc_attached(self, obj):
        try:
            if len(obj.stripe.cards.all()) > 0:
                return 'Yes'
        except:
            pass
        return '--'

    cc_attached.short_description = 'Credit card attached'

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super(AccountAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    readonly_fields = ('number_installations', 'cc_attached')

    model = models.Account

    list_display = (
        'id', 'business_name', 'primary_contact',
        'payment_on_platform', 'cc_attached', 'number_installations'
    )

    actions = [sync_license_records]


admin.site.register(models.Account, AccountAdmin)


class EcommerceUserAdmin(UserAdmin):

    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_admin', 'is_active')
    ordering = ('-id',)
    search_fields = ('email',)
    readonly_fields = ('date_joined', 'is_primary_contact')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'username', 'account', 'is_primary_contact')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_admin',)}),
        ('Additional Info', {'fields': ('is_active', 'date_joined', 'idp_uuid')}),
    )
    filter_horizontal = ()
    list_filter = ()

    def has_add_permission(self, request):
        return False

admin.site.unregister(Group)

admin.site.register(models.EcommerceUser, EcommerceUserAdmin)


class ActivationAdmin(admin.ModelAdmin):

    model = models.Activation

    list_display = ('id', 'user', 'activation_key', 'created')

admin.site.register(models.Activation, ActivationAdmin)


class InvitationAdmin(admin.ModelAdmin):

    model = models.Invitation

    list_display = ('id', 'email', 'invited_by', 'activation_key', 'created')

admin.site.register(models.Invitation, InvitationAdmin)


class CreditAdmin(admin.ModelAdmin):

    model = models.Credit

    list_display = (
        'id', 'initial_amount', 'remaining_amount',
        'created', 'account', 'expires'
    )

admin.site.register(models.Credit, CreditAdmin)


class PremiumInvitationAdmin(admin.ModelAdmin):

    form = PremiumInvitationAdminForm
    model = models.PremiumInvitation

    list_display = ('email', 'activation_key', 'created')
    readonly_fields = ('activation_key', )

    def save_model(self, request, obj, form, change):

        if not obj.activation_key:

            obj.activation_key = generate_activation_key(obj.email)
            obj.save()
            send_premium_invitation(obj)

admin.site.register(models.PremiumInvitation, PremiumInvitationAdmin)
