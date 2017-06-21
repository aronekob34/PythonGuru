import logging
import stripe

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from account import constants
from account.utils import send_billing_email, send_charging_failed_email

from payment.models import Payment
from payment.constants import INITIATED, PAID, FAILED

stripe.api_key = settings.STRIPE_API_KEY

logger = logging.getLogger('billing')


class Command(BaseCommand):

    def handle(self, *args, **options):

        payments = Payment.objects.filter(status=INITIATED)

        for payment in payments:

            try:

                account = payment.account

                logger.info('Running monthly payment for {}'.format(account.get_name()))

                if payment.paid_amount > 0:

                    response = stripe.Charge.create(
                        amount=int(payment.paid_amount * 100),
                        currency='USD',
                        customer=account.stripe.customer_id,
                        description=constants.CHARGE_DESCIRPTION.format(account.get_name())
                    )

                    payment.stripe_reference = response.id
                    send_billing_email(payment)

                payment.status = PAID
                payment.save()

                logger.info('Payment successful')

            except ObjectDoesNotExist as e:

                payment.status = FAILED
                payment.save()
                logger.error('No card attached to account {}, {}'.format(account, e))

            except (stripe.error.CardError, stripe.error.StripeError) as e:

                payment.status = FAILED
                payment.save()

                customer = stripe.Customer.retrieve(account.stripe.customer_id)
                card_details = customer.sources.retrieve(customer.default_source)

                send_charging_failed_email(payment, card_details.last4)
                logger.error('Card has been declined: account {}, {}'.format(account, e))

            except Exception as e:
                logger.exception(e)
                logger.error('Billing failed: account {}, {}'.format(account, e))
