import logging
import random
from hashlib import sha1

import datetime

from smtplib import SMTPRecipientsRefused


from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import smart_bytes
from django.utils.six import text_type


logger = logging.getLogger('django')


def get_last_month():

    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    return last_month.month, last_month.year


def generate_sha1(string, salt=None):

    if not isinstance(string, (str, text_type)):
        string = str(string)

    if not salt:
        salt = sha1(str(random.random()).encode('utf-8')).hexdigest()[:5]

    salted_bytes = (smart_bytes(salt) + smart_bytes(string))
    hash_ = sha1(salted_bytes).hexdigest()

    return salt, hash_


def send_mail(subject_template_name, email_template_name, to_email, context=None,
              html_email_template_name=None, from_email=settings.DEFAULT_FROM_EMAIL,
              bcc=None, connection=None):

    try:
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        if not isinstance(to_email, list):
            to_email = [to_email]

        if settings.DEBUG and settings.LIVE_EMAIL:

            email_message = EmailMultiAlternatives(
                subject, body, from_email, [settings.RECIPIENT_TEST_EMAIL], connection=connection
            )

        else:

            email_message = EmailMultiAlternatives(
                subject, body, from_email, to_email, bcc, connection=connection
            )

        if settings.TEST_TEXT_EMAIL:
            email_message.send()

        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()

    except SMTPRecipientsRefused as e:
        logger.error(e)

    except Exception as e:
        message = 'Failed to send email to {}, Subject: {}, Exception: {}'.format(
            to_email, subject_template_name, e)
        logger.exception(message)
