import logging
import datetime

from calendar import month_name

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import get_connection

from gluu_ecommerce.utils import send_mail, generate_sha1

from account.connectors.idp_interface import email_exists
from account.models import Invitation


logger = logging.getLogger('django')


def send_activation_email(user, key):

    activation_link = '{}://{}{}'.format(
        settings.PROTOCOL,
        settings.DOMAIN,
        reverse('account:activate', kwargs={'activation_key': key})
    )

    context = {
        'activation_link': activation_link,
        'name': user.first_name
    }

    send_mail(
        subject_template_name='emails/activate/verify_email_subject.txt',
        email_template_name='emails/activate/verify_email.txt',
        to_email=user.email,
        context=context,
        html_email_template_name='emails/activate/verify_email.html'
    )


def generate_activation_key(email):

    _, activation_key = generate_sha1(email)
    return activation_key


def send_invitation(invitation):

    existing = email_exists(invitation.email)

    if existing:

        invitation_link = '{}://{}{}?next={}'.format(
            settings.PROTOCOL,
            settings.DOMAIN,
            reverse('social:begin', args=['gluu']),
            reverse('account:accept-invite', kwargs={'activation_key': invitation.activation_key})
        )

    else:

        invitation_link = '{}://{}{}'.format(
            settings.PROTOCOL,
            settings.DOMAIN,
            reverse('account:register-invite', kwargs={'activation_key': invitation.activation_key})
        )

    context = {
        'invited_by': invitation.invited_by.get_full_name(),
        'account': invitation.invited_by.account.get_name(),
        'invitation_link': invitation_link,
        'existing': existing
    }

    send_mail(
        subject_template_name='emails/invite/invite_billing_admin_subject.txt',
        email_template_name='emails/invite/invite_billing_admin.txt',
        to_email=invitation.email,
        context=context,
        html_email_template_name='emails/invite/invite_billing_admin.html'
    )


def send_premium_invitation(invitation):

    existing = email_exists(invitation.email)

    if existing:

        invitation_link = '{}://{}{}?next={}'.format(
            settings.PROTOCOL,
            settings.DOMAIN,
            reverse('social:begin', args=['gluu']),
            reverse('account:register-premium-auth', kwargs={'activation_key': invitation.activation_key}),
        )

    else:

        invitation_link = '{}://{}{}'.format(
            settings.PROTOCOL,
            settings.DOMAIN,
            reverse('account:register-premium', kwargs={'activation_key': invitation.activation_key}),
        )

    context = {
        'invitation_link': invitation_link,
        'existing': existing
    }

    send_mail(
        subject_template_name='emails/invite/invite_premium_subject.txt',
        email_template_name='emails/invite/invite_premium.txt',
        to_email=invitation.email,
        context=context,
        html_email_template_name='emails/invite/invite_premium.html'
    )


def create_invite(email, invited_by):

    invitations = Invitation.objects.filter(email=email).exclude(
        activation_key__in=['REVOKED', 'ACTIVATED', 'EXPIRED'])

    if len(invitations) > 1:
        logger.error('More than one active invite for email {}'.format(email))

    elif len(invitations) == 1:
        invitations[0].activation_key = 'EXPIRED'
        invitations[0].save()

    activation_key = generate_activation_key(email)

    invitation = Invitation(
        email=email,
        invited_by=invited_by,
        activation_key=activation_key
    )

    invitation.save()

    send_invitation(invitation)


def send_summary_email(payment, record, last_4=None):

    billing_management_link = '{}://{}{}'.format(
        settings.PROTOCOL,
        settings.DOMAIN,
        reverse('payment:view-cards')
    )

    connection = get_connection(
        username=settings.EMAIL_HOST_USER_BILLING,
        password=settings.EMAIL_HOST_PASSWORD_BILLING
    )

    billing_date = '7th {} {}'.format(
        month_name[datetime.date.today().month], datetime.date.today().year)

    context = {
        'billing_date': billing_date,
        'account_name': payment.account.get_name(),
        'billing_management_link': billing_management_link,
        'last_4': last_4,
        'payment': payment,
        'record': record
    }

    recipients = payment.account.billing_admins.values_list('email', flat=True)
    to_emails = [c for c in recipients]

    send_mail(
        subject_template_name='emails/billing/monthly_summary_subject.txt',
        email_template_name='emails/billing/monthly_summary.txt',
        to_email=to_emails,
        bcc=[settings.BILLING_BCC, ],
        context=context,
        from_email=settings.BILLING_EMAIL,
        html_email_template_name='emails/billing/monthly_summary.html',
        connection=connection
    )


def send_billing_email(payment):

    connection = get_connection(
        username=settings.EMAIL_HOST_USER_BILLING,
        password=settings.EMAIL_HOST_PASSWORD_BILLING
    )

    context = {
        'account_name': payment.account.get_name(),
        'date': datetime.date.today(),
        'payment': payment
    }

    recipients = payment.account.billing_admins.values_list('email', flat=True)
    to_emails = [c for c in recipients]

    send_mail(
        subject_template_name='emails/billing/payment_made_subject.txt',
        email_template_name='emails/billing/payment_made.txt',
        to_email=to_emails,
        bcc=[settings.BILLING_BCC, ],
        context=context,
        from_email=settings.BILLING_EMAIL,
        html_email_template_name='emails/billing/payment_made.html',
        connection=connection
    )


def send_charging_failed_email(payment, last_4):

    connection = get_connection(
        username=settings.EMAIL_HOST_USER_BILLING,
        password=settings.EMAIL_HOST_PASSWORD_BILLING
    )

    billing_date = '14th {} {}'.format(
        month_name[datetime.date.today().month], datetime.date.today().year)

    context = {
        'payment': payment,
        'billing_date': billing_date,
        'last_4': last_4
    }

    recipients = payment.account.billing_admins.values_list('email', flat=True)
    to_emails = [c for c in recipients]

    send_mail(
        subject_template_name='emails/billing/charging_failed_subject.txt',
        email_template_name='emails/billing/charging_failed.txt',
        to_email=to_emails,
        bcc=[settings.BILLING_BCC, ],
        context=context,
        from_email=settings.BILLING_EMAIL,
        html_email_template_name='emails/billing/charging_failed.html',
        connection=connection
    )


def send_license_deactivated_email(payment, last_4):

    connection = get_connection(
        username=settings.EMAIL_HOST_USER_BILLING,
        password=settings.EMAIL_HOST_PASSWORD_BILLING
    )

    context = {
        'payment': payment,
        'last_4': last_4
    }

    recipients = payment.account.billing_admins.values_list('email', flat=True)
    to_emails = [c for c in recipients]

    send_mail(
        subject_template_name='emails/billing/license_deactivated_subject.txt',
        email_template_name='emails/billing/license_deactivated.txt',
        to_email=to_emails,
        bcc=[settings.BILLING_BCC, ],
        context=context,
        from_email=settings.BILLING_EMAIL,
        html_email_template_name='emails/billing/license_deactivated.html',
        connection=connection
    )

def send_new_account_notification(account):

    send_mail(
        subject_template_name='emails/new_account/new_account_subject.txt',
        email_template_name='emails/new_account/new_account.txt',
        to_email=settings.NEW_ACCOUNT_EMAIL,
        context={'account': account},
        html_email_template_name='emails/new_account/new_account.html'
    )
