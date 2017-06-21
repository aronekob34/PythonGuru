from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from django_countries.fields import CountryField

from localflavor.us.models import USStateField, USZipCodeField


class Account(models.Model):

    business_name = models.CharField(
        'Business Name',
        max_length=100,
        blank=True
    )

    primary_contact = models.OneToOneField(
        'EcommerceUser',
        related_name='primary_account'
    )

    address_1 = models.CharField(
        'Address Line 1',
        max_length=100
    )

    address_2 = models.CharField(
        'Address Line 2',
        max_length=100,
        blank=True
    )

    city = models.CharField(
        'City',
        max_length=100
    )

    state = USStateField(blank=True)

    zip_code = USZipCodeField(blank=True)

    country = CountryField()

    payment_on_platform = models.BooleanField(default=True)

    def __str__(self):
        if self.business_name:
            return self.business_name
        return self.primary_contact.get_full_name()

    def get_name(self):
        if self.business_name:
            return self.business_name
        return self.primary_contact.get_full_name()

    def account_type(self):
        if self.business_name:
            return 'Business'
        return 'Individual'

    @property
    def balance(self):

        try:
            no_licenses = self.license.records.aggregate(
                models.Sum('number_licenses'))['number_licenses__sum']
        except ObjectDoesNotExist:
            pass

        try:
            paid = self.payments.filter(status='PAID').aggregate(
                models.Sum('amount'))['amount__sum']
        except ObjectDoesNotExist:
            pass

        if not no_licenses:
            no_licenses = 0

        if not paid:
            paid = 0.0

        return (no_licenses * settings.PRICE_PER_LICENSE) - paid

    @property
    def remaining_credits(self):

        remaining_amount = Credit.objects.filter(
            account=self,
            expires__gt=timezone.now(),
            remaining_amount__gt=0.00
        ).aggregate(models.Sum('remaining_amount'))['remaining_amount__sum']

        if not remaining_amount:
            return 0.00

        return remaining_amount

    @property
    def number_installations(self):

        try:
            if self.license.records.all():
                return self.license.records.aggregate(models.Sum('number_licenses'))['number_licenses__sum']
        except ObjectDoesNotExist:
            pass
        return 0


class EcommerceUserManager(BaseUserManager):

    def create_user(self, email, password=None, **kwargs):

        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email), **kwargs)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):

        user = self.create_user(email=email, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class EcommerceUser(AbstractBaseUser):

    objects = EcommerceUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        related_name='billing_admins'
    )

    email = models.EmailField(
        'Email address',
        max_length=255,
        unique=True,
        help_text='Email address'
    )

    username = models.CharField(
        max_length=75,
        blank=True,
        default=''
    )

    first_name = models.CharField(
        'First name',
        max_length=75,
        help_text='First name'
    )

    last_name = models.CharField(
        'Last name',
        max_length=75,
        help_text='Last name'
    )

    phone_number = models.CharField(
        'phone number',
        max_length=30,
        help_text='Phone number'
    )

    date_joined = models.DateTimeField(
        'date joined',
        auto_now=True
    )

    is_active = models.BooleanField(default=True)

    is_admin = models.BooleanField(default=False)

    idp_uuid = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    def get_full_name(self):
        return u'{} {}'.format(self.first_name, self.last_name)

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def is_primary_contact(self):
        try:
            self.primary_account
            return True
        except ObjectDoesNotExist:
            return False


class Activation(models.Model):

    user = models.OneToOneField(
        EcommerceUser,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name='activation'
    )

    activation_key = models.CharField(
        'activation key',
        max_length=40
    )

    created = models.DateTimeField(
        'created',
        auto_now_add=True
    )


class Invitation(models.Model):

    email = models.EmailField(
        blank=False,
        null=False,
        unique=False
    )

    invited_by = models.ForeignKey(
        EcommerceUser,
        blank=False,
        null=False,
        unique=False,
        related_name='invites'
    )

    activation_key = models.CharField(
        'activation key',
        max_length=40
    )

    created = models.DateTimeField(
        'created',
        auto_now_add=True
    )


class Credit(models.Model):

    created = models.DateTimeField(auto_now_add=True)

    remaining_amount = models.FloatField()

    initial_amount = models.FloatField()

    account = models.ForeignKey(
        Account,
        related_name='credits',
        blank=False,
        null=False
    )

    expires = models.DateTimeField()

    @property
    def is_expired(self):
        return self.expires < timezone.now()


class PremiumInvitation(models.Model):

    email = models.EmailField(
        blank=False,
        null=False,
        unique=False
    )

    activation_key = models.CharField(
        'activation key',
        blank=True,
        max_length=40
    )

    created = models.DateTimeField(
        'created',
        auto_now_add=True
    )
