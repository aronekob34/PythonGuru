from __future__ import unicode_literals

import jsonfield

from django.db import models

from account.models import Account
from payment import constants


class StripeCustomer(models.Model):

    customer_id = models.CharField(
        max_length=100,
        unique=True
    )

    account = models.OneToOneField(
        Account,
        related_name='stripe'
    )


class StripeCard(models.Model):

    card_id = models.CharField(
        max_length=100,
        unique=True
    )

    customer = models.ForeignKey(
        StripeCustomer,
        related_name='cards'
    )

    is_primary = models.BooleanField(
        default=True
    )


class Payment(models.Model):

    created = models.DateTimeField(
        auto_now_add=True
    )

    invoice_id = models.CharField(
        max_length=100,
        unique=True
    )

    account = models.ForeignKey(
        Account,
        related_name='payments',
        blank=False,
        null=False
    )

    stripe_reference = models.CharField(
        blank=True,
        max_length=40
    )

    license_record = models.ForeignKey

    amount = models.FloatField()

    credits_used = models.FloatField(default=0.00)

    details = jsonfield.JSONField()

    status = models.CharField(
        max_length=4,
        choices=constants.PAYMENT_STATUS_CHOICES,
        default=constants.INITIATED
    )

    month = models.IntegerField()

    year = models.IntegerField()

    @property
    def paid_amount(self):
        return self.amount - self.credits_used
