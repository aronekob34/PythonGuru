import json
import logging
import datetime
import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from social.apps.django_app.default.models import UserSocialAuth

from account.constants import GENERIC_ERROR_DESCRIPTION_REGISTRATION as GENERIC_ERROR_DESC
from account import constants
from account import forms
from account.connectors import idp_interface as idp
from account.models import Activation, EcommerceUser, Invitation, Credit, PremiumInvitation
from account.utils import (send_activation_email, create_invite, generate_activation_key,
                           send_new_account_notification)

from payment.models import Payment

from gluu_license.connectors.license_interface import (
    acquire_license, get_usage_records, retrieve_active_installations)
from gluu_license.models import License

logger = logging.getLogger('django')
stripe.api_key = settings.STRIPE_API_KEY


def register(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('account:register-authenticated'))

    if request.method == 'GET':

        user_form = forms.RegisterUserForm()
        account_form = forms.RegisterAccountForm()

    elif request.method == 'POST':

        try:

            user_form = forms.RegisterUserForm(request.POST)
            account_form = forms.RegisterAccountForm(request.POST)

            if user_form.is_valid() and account_form.is_valid():

                user = user_form.save(commit=False)
                user.is_active = False
                user.save()

                user.idp_uuid = idp.create_user(
                    user=user,
                    password=user_form.cleaned_data.get('password1')
                )

                user.save()

                activation_key = generate_activation_key(user.email)
                activation = Activation(user=user, activation_key=activation_key)
                activation.save()

                send_activation_email(user, activation_key)

                account = account_form.save(commit=False)
                account.primary_contact = user
                account.save()

                user.account = account
                user.save()

                send_new_account_notification(account)

                return render(request, 'account/registration_complete.html', {'email': user.email})

        except Exception as e:

            logger.exception(e)
            return render(request, 'error.html', GENERIC_ERROR_DESC)

    return render(request, 'account/register.html', {
        'account_form': account_form, 'user_form': user_form})


def register_authenticated(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('account:register'))

    if request.user.account:
        return HttpResponseRedirect(reverse('account:dashboard'))

    if request.method == 'GET':
        account_form = forms.RegisterAccountForm()

    elif request.method == 'POST':

        try:
            user = request.user
            account_form = forms.RegisterAccountForm(request.POST)

            if account_form.is_valid():

                account = account_form.save(commit=False)
                account.primary_contact = request.user
                account.save()

                user.account = account
                user.save()

                send_new_account_notification(account)

                return HttpResponseRedirect(reverse('account:dashboard'))

        except Exception as e:

            logger.exception(e)
            return render(request, 'error.html', GENERIC_ERROR_DESC)

    return render(request, 'account/register.html', {'account_form': account_form})


def register_invited(request, activation_key):

    if request.user.is_authenticated():
        logout(request)

    try:
        invitation = Invitation.objects.get(activation_key=activation_key)

    except ObjectDoesNotExist:

        return render(request, 'error.html', {
            'error': 'Invitation Key not recognized',
            'description': 'Sorry, we did not recognize that invitation key. \
                            It either has been used before or is invalid.',
        })

    registration_form = forms.RegisterInvitedUserForm()

    if request.method == 'POST':

        registration_form = forms.RegisterInvitedUserForm(request.POST)

        try:

            if registration_form.is_valid():

                user = registration_form.save(commit=False)
                user.account = invitation.invited_by.account
                user.save()

                user.idp_uuid = idp.create_user(
                    user=user,
                    password=registration_form.cleaned_data.get('password1'),
                    active=True
                )
                user.save()

                invitation.activation_key = 'ACTIVATED'
                invitation.save()

                return render(request, 'account/activation_complete.html')

        except Exception as e:

            logger.error('Registration Failed: {}'.format(e))
            return render(request, 'error.html', GENERIC_ERROR_DESC)

    registration_form.fields['email'].initial = invitation.email

    return render(request, 'account/register_user.html',
                  {'registration_form': registration_form,
                   'activation_key': activation_key})


def register_premium(request, activation_key):

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('account:register-premium-auth', kwargs={'activation_key': activation_key}))

    try:

        invitation = PremiumInvitation.objects.get(activation_key=activation_key)

    except ObjectDoesNotExist:

        messages.error(request, 'Invalid activation key. Please contact support@gluu.org for help.')
        return HttpResponseRedirect(reverse('home'))

    user_form = forms.RegisterInvitedUserForm()
    user_form.fields['email'].initial = invitation.email
    account_form = forms.RegisterAccountForm()

    if request.method == 'POST':

        try:
            user_form = forms.RegisterUserForm(request.POST)
            account_form = forms.RegisterAccountForm(request.POST)

            if user_form.is_valid() and account_form.is_valid():

                user = user_form.save(commit=False)
                user.save()

                user.idp_uuid = idp.create_user(
                    user=user,
                    password=user_form.cleaned_data.get('password1'),
                    active=True
                )

                user.save()

                account = account_form.save(commit=False)
                account.primary_contact = user
                account.payment_on_platform = False
                account.save()

                user.account = account
                user.save()

                invitation.activation_key = 'ACTIVATED'
                invitation.save()

                send_new_account_notification(account)

                return render(request, 'account/activation_complete.html', {'email': user.email})

        except Exception as e:

            logger.exception(e)
            return render(request, 'error.html', GENERIC_ERROR_DESC)

    return render(request, 'account/registration_premium.html', {
        'user_form': user_form, 'account_form': account_form, 'activation_key': activation_key})


def register_premium_auth(request, activation_key):

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('account:register-premium', kwargs={'activation_key': activation_key}))

    try:
        invitation = PremiumInvitation.objects.get(activation_key=activation_key)

    except ObjectDoesNotExist:
        messages.error(request, 'Invalid activation key. Please contact support@gluu.org for help.')
        return HttpResponseRedirect(reverse('home'))

    if request.user.email != invitation.email:

        messages.error(request, 'This email does not match the invitation email')
        return HttpResponseRedirect(reverse('account:logout'))

    if request.user.account:

        messages.error(request, 'This user is already associated with another account')
        return HttpResponseRedirect(reverse('account:dashboard'))

    account_form = forms.RegisterAccountForm()

    if request.method == 'POST':

        try:

            account_form = forms.RegisterAccountForm(request.POST)

            if account_form.is_valid():

                account = account_form.save(commit=False)
                account.primary_contact = request.user
                account.payment_on_platform = False
                account.save()
                request.user.account = account
                request.user.save()

                invitation.activation_key = 'ACTIVATED'
                invitation.save()

                send_new_account_notification(account)

                return HttpResponseRedirect(reverse('account:dashboard'))

        except Exception as e:

            logger.exception(e)
            return render(request, 'error.html', GENERIC_ERROR_DESC)

    return render(request, 'account/registration_premium.html', {
        'account_form': account_form, 'activation_key': activation_key})


@require_GET
def activate(request, activation_key):

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('account:register-authenticated'))

    try:

        activation = Activation.objects.get(activation_key=activation_key)
        activation.activation_key = 'ACTIVATED'
        activation.save()

        user = activation.user
        user.is_active = True
        user.save()

        idp.activate_user(user)

        return render(request, 'account/activation_complete.html')

    except Exception as e:

        logger.exception(e)

        return render(request, 'error.html', {
            'error': 'Activation Failed',
            'description': 'Sorry, we did not recognize that activation key. \
                            It either has been used before or is invalid.',
        })


def logout_view(request):

    if request.user:

        try:
            user_social = UserSocialAuth.objects.get(uid=request.user.email)

            try:
                id_token_hint = user_social.extra_data['id_token']

            except TypeError:
                id_token_hint = json.loads(user_social.extra_data)['id_token']

            ox_auth_end_session_url = settings.SOCIAL_AUTH_END_SESSION_ENDPOINT
            post_logout_redirect_uri = settings.SOCIAL_AUTH_POST_LOGOUT_REDIRECT_URL

            logout_url = '{}/?id_token_hint={}&post_logout_redirect_uri={}'.format(
                ox_auth_end_session_url, id_token_hint, post_logout_redirect_uri)

            logout(request)

            return HttpResponseRedirect(logout_url)

        except ObjectDoesNotExist:

            logger.error('Logout Failed: Social Auth Credentials for {} could not be found'.format(request.user.email))

        except Exception as e:

            logger.error('Logout Failed, Message {}'.format(e.message))

        logout(request)

    return HttpResponseRedirect(reverse('home'))


@login_required
@require_GET
def dashboard(request):

    if not request.user.account:
        return HttpResponseRedirect(reverse('account:register-authenticated'))

    try:
        request.user.account.license

    except ObjectDoesNotExist:

        account = request.user.account

        if request.user.account.payment_on_platform:

            credit = Credit(
                initial_amount=constants.INITAL_CREDIT,
                remaining_amount=constants.INITAL_CREDIT,
                account=account,
                expires=timezone.now() + datetime.timedelta(
                    days=constants.INITAL_CREDIT_EXPIRATION)
            )
            credit.save()

        license = acquire_license(account.get_name())
        license = License(
            license_id=license['license_id'],
            license_password=license['license_password'],
            public_password=license['public_password'],
            public_key=license['public_key'],
            account=account,
            expiration_date=license['expiration_date'],
            creation_date=license['creation_date']
        )
        license.save()

    billing_admins = request.user.account.billing_admins.all()
    invitation_form = forms.InvitationForm()
    invites = Invitation.objects.filter(invited_by=request.user).exclude(
        activation_key__in=['REVOKED', 'ACTIVATED', 'EXPIRED'])

    license_records = get_usage_records(request.user.account.license)
    active_mac_addresses = retrieve_active_installations(request.user.account.license.license_id)

    last_payment = None

    if request.user.account.payment_on_platform:

        payments = Payment.objects.filter(
            account=request.user.account, status='PAID').order_by('-created')

        if payments:
            last_payment = payments[0]

    return render(
        request, 'account/dashboard.html',
        {'invitation_form': invitation_form,
         'billing_admins': billing_admins,
         'invites': invites,
         'license_records': license_records,
         'last_payment': last_payment,
         'active_mac_addresses': active_mac_addresses}
    )


@login_required
@require_POST
def send_invite(request):

    invitation_form = forms.InvitationForm(request.POST)

    if invitation_form.is_valid():

        email = invitation_form.cleaned_data.get('email')

        try:

            user = EcommerceUser.objects.get(email=email)

            if user.account:
                messages.error(request, 'This email is already associated with another account.')
            else:
                user.account = request.user.account
                user.save()
                messages.success(request, 'User has been added your account.')

        except ObjectDoesNotExist:

            try:
                create_invite(email, request.user)
                messages.success(request, 'Your invitation has been sent.')

            except Exception:
                messages.error('Something went wrong. Please contact support@gluu.org')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@require_GET
@login_required
def revoke_invite(request, invite_id):

    try:

        invite = Invitation.objects.get(id=invite_id)

        if invite.invited_by.account == request.user.account:

            invite.activation_key = 'REVOKED'
            invite.save()

    except ObjectDoesNotExist as e:

        logger.error(e)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@require_GET
@login_required
def revoke_access(request, user_id):

    try:
        user = EcommerceUser.objects.get(id=user_id)

        if user.account == request.user.account:

            user.account = None
            user.save()

        else:
            logger.error('Billing admin does not belong to same account')

    except ObjectDoesNotExist as e:

        logger.error(e)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def view_profile(request):

    invitation_form = forms.InvitationForm()
    billing_admins = request.user.account.billing_admins.all()
    invites = Invitation.objects.filter(invited_by=request.user).exclude(
        activation_key__in=['REVOKED', 'ACTIVATED', 'EXPIRED'])

    return render(
        request, 'account/view_profile.html',
        {'invitation_form': invitation_form,
         'billing_admins': billing_admins,
         'invites': invites}
    )


@login_required
def edit_profile(request):

    try:

        if request.method == 'GET':
            account_form = forms.EditAccountForm(instance=request.user.account)

            if request.user.account.account_type == 'Individual':
                del account_form.fields['business_name']

        elif request.method == 'POST':
            account_form = forms.EditAccountForm(request.POST, instance=request.user.account)

            if account_form.is_valid():
                account_form.save()
                return HttpResponseRedirect(reverse('account:view-profile'))

    except ObjectDoesNotExist:
        logger.error('No account profile found for user {}'.format(request.user))
        return HttpResponseServerError()

    return render(request, 'account/edit_profile.html', {'account_form': account_form})


@login_required
def accept_invite(request, activation_key):

    try:

        invitation = Invitation.objects.get(activation_key=activation_key)

        if request.user.email != invitation.email:

            return render(request, 'error.html', {
                'error': 'Email Mismatch',
                'description': 'The invitation was not sent to that email.'
            })

        user = request.user

        user.account = invitation.invited_by.account
        user.save()
        invitation.activation_key = 'ACTIVATED'
        invitation.save()

        return HttpResponseRedirect(reverse('account:dashboard'))

    except Exception as e:

        logger.exception(e)

        return render(request, 'error.html', {
            'error': 'Invitation Key not recognized',
            'description': 'Sorry, we did not recognize that invitation key. \
                            It either has been used before or is invalid.',
        })
