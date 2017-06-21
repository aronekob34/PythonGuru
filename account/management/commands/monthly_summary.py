import logging
import stripe
from random import randint

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import timezone

from account.models import Account
from account.utils import send_summary_email

from payment.models import Payment, StripeCustomer

from gluu_ecommerce.utils import get_last_month

from gluu_license.models import LicenseRecord
from gluu_license.connectors.license_interface import sync_usage_records

stripe.api_key = settings.STRIPE_API_KEY

logger = logging.getLogger('billing')


class Command(BaseCommand):

    def handle(self, *args, **options):

        accounts = Account.objects.filter(payment_on_platform=True)

        month, year = get_last_month()

        for account in accounts:

            try:
                logger.info('Next account {} ({}).'.format(account.id, account.get_name()))

                sync_usage_records(account.license)

                record = LicenseRecord.objects.get(
                    license=account.license,
                    month=month,
                    year=year
                )

                logger.info('Last month\'s charge {}'.format(record.total_usd))

                details = {}
                for mac, count in record.details.iteritems():
                    details[mac] = [count, count * settings.PRICE_PER_LICENSE]

                payment = Payment(
                    invoice_id=randint(100000000, 999999999),
                    account=account,
                    amount=record.total_usd,
                    details=details,
                    month=month,
                    year=year
                )

                credits = account.credits.filter(
                    expires__gt=timezone.now(),
                    remaining_amount__gt=0.00
                )

                # For now, we only support one valid credit object at a time
                if len(credits) == 1:

                    credit = credits[0]

                    if credit.remaining_amount > record.total_usd:
                        payment.credits_used = record.total_usd
                        credit.remaining_amount = credit.remaining_amount - record.total_usd

                    else:  # credit.remaining_amount <= self.balance:
                        payment.credits_used = credit.remaining_amount
                        credit.remaining_amount = 0.00

                    credit.save()

                payment.save()

                if len(StripeCustomer.objects.filter(account=account)) == 1:

                    customer = stripe.Customer.retrieve(account.stripe.customer_id)
                    card_details = customer.sources.retrieve(customer.default_source)
                    send_summary_email(payment, record, card_details.last4)

                else:
                    send_summary_email(payment, record)

            except ObjectDoesNotExist as e:
                logger.info('No license record found for account {}, {}'.format(account, e))

            except Exception as e:
                logger.exception(e)
                logger.error('Billing failed: account {}, {}'.format(account, e))
