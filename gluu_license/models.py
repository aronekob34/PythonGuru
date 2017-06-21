from __future__ import unicode_literals

import jsonfield

from django.conf import settings
from django.db import models

from account.models import Account
from payment.models import Payment
from payment import constants


class License(models.Model):

    license_id = models.CharField(
        max_length=100,
        unique=True
    )

    account = models.OneToOneField(
        Account,
        related_name='license'
    )

    license_password = models.CharField(
        max_length=100
    )

    public_password = models.CharField(
        max_length=100
    )

    public_key = models.CharField(
        max_length=500
    )

    is_active = models.BooleanField(
        default=True
    )

    is_blocked = models.BooleanField(
        default=False
    )

    creation_date = models.DateTimeField()

    expiration_date = models.DateTimeField()

    def __str__(self):
        return self.license_id


class LicenseRecord(models.Model):

    license = models.ForeignKey(License, related_name='records')

    created = models.DateTimeField(auto_now_add=True)

    month = models.IntegerField()

    year = models.IntegerField()

    number_licenses = models.IntegerField()

    details = jsonfield.JSONField()

    @property
    def total_usd(self):
        return settings.PRICE_PER_LICENSE * self.number_licenses

    @property
    def no_mac(self):
        return len(self.details)

    @property
    def paid(self):

        try:

            return Payment.objects.get(
                account=self.license.account, month=self.month,
                year=self.year).status == constants.PAID

        except:
            return False
