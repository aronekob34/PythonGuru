from django.contrib import admin
from payment import models


class CardInlineAdmin(admin.StackedInline):
    model = models.StripeCard
    extra = 0
    list_display = ('card_id', 'primary_card', 'exp_month', 'exp_year')


class StripeCustomerAdmin(admin.ModelAdmin):

    model = models.StripeCustomer
    list_display = ('id', 'customer_id', 'account',)
    inlines = [CardInlineAdmin, ]

admin.site.register(models.StripeCustomer, StripeCustomerAdmin)


class PaymentAdmin(admin.ModelAdmin):

    model = models.Payment

    readonly_fields = ('created', )

    list_display = (
        'id', 'invoice_id', 'created', 'amount', 'account',
        'credits_used', 'stripe_reference', 'status'
    )

admin.site.register(models.Payment, PaymentAdmin)
