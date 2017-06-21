import logging
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.views.decorators.http import require_GET

from payment.models import StripeCard, StripeCustomer
from payment.utils import is_expired

import stripe

logger = logging.getLogger('django')
stripe.api_key = settings.STRIPE_API_KEY


@login_required
def get_primary_card_details(request):

    if not request.user.account.stripe:

        return HttpResponse(
            json.dumps({}),
            content_type='application/json'
        )

    try:

        customer_id = request.user.account.stripe.customer_id
        customer = stripe.Customer.retrieve(customer_id)
        card_details = customer.sources.retrieve(customer.default_source)

    except Exception as e:
        logger.exception(e)
        card_details = {}

    return HttpResponse(
        json.dumps(card_details),
        content_type='application/json'
    )


@login_required
def view_cards(request):

    if not request.user.account.payment_on_platform:
        return HttpResponseRedirect(reverse('account:dashboard'))

    try:

        if request.user.account.stripe:
            customer = stripe.Customer.retrieve(request.user.account.stripe.customer_id)
            cards = customer.sources.all(object='card')

            for c in cards:
                if c['id'] == customer.default_source:
                    c['is_primary'] = True
                else:
                    c['is_primary'] = False
                c['db_id'] = StripeCard.objects.get(card_id=c['id']).id
                c['is_expired'] = is_expired(c['exp_year'], c['exp_month'])

    except ObjectDoesNotExist:
        return render(request, 'payment/view_cards.html')

    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError(e)

    return render(request, 'payment/view_cards.html', {'cards': cards})


@login_required
def add_card(request):

    if not request.user.account.payment_on_platform:
        return HttpResponseRedirect(reverse('account:dashboard'))

    if request.method == 'POST':

        try:
            token = request.POST.get('stripeToken', None)

            if not token:

                logger.error(
                    'No token received when creating a card. Account was {}'.format(
                        request.user.account.id)
                )

                messages.error(
                    request,
                    'Sorry, we could not add the card. Please reach out to support@gluu.org for help.'
                )

                return render(
                    request, 'payment/add_card.html',
                    {'stripe_public_key': settings.STRIPE_PUBLIC_KEY}
                )

            try:
                stripe_customer = request.user.account.stripe
                customer = stripe.Customer.retrieve(stripe_customer.customer_id)
                card = customer.sources.create(card=token)

                card = StripeCard(
                    card_id=card.id,
                    customer=stripe_customer,
                    is_primary=False
                )

                card.save()

            except ObjectDoesNotExist:

                customer = stripe.Customer.create(source=token)
                stripe_customer = StripeCustomer(account=request.user.account, customer_id=customer.id)
                stripe_customer.save()

                card = StripeCard(
                    card_id=customer.default_source,
                    customer=stripe_customer,
                    is_primary=True
                )

                card.save()

            return HttpResponseRedirect(reverse('payment:view-cards'))

        except stripe.error.CardError as e:
            messages.error(request, e.message)

    return render(request, 'payment/add_card.html', {'stripe_public_key': settings.STRIPE_PUBLIC_KEY})


@login_required
@require_GET
def make_primary_card(request, card_id):

    if not request.user.account.payment_on_platform:
        return HttpResponseRedirect(reverse('account:dashboard'))

    try:
        old_primary = StripeCard.objects.get(customer=request.user.account.stripe, is_primary=True)
        old_primary.is_primary = False
        old_primary.save()

        new_primary = StripeCard.objects.get(id=card_id, customer=request.user.account.stripe)
        new_primary.is_primary = True
        new_primary.save()

        customer = stripe.Customer.retrieve(request.user.account.stripe.customer_id)
        customer.default_source = new_primary.card_id
        customer.save()

    except Exception as e:
        logger.exception(e)

    return HttpResponseRedirect(reverse('payment:view-cards'))


@login_required
@require_GET
def delete_card(request, card_id):

    if not request.user.account.payment_on_platform:
        return HttpResponseRedirect(reverse('account:dashboard'))

    try:
        deleted_card = StripeCard.objects.get(id=card_id, customer=request.user.account.stripe)

        customer = stripe.Customer.retrieve(request.user.account.stripe.customer_id)
        response = customer.sources.retrieve(deleted_card.card_id).delete()

        if not response['deleted']:
            logger.error('Failed to delete card {}'.format(deleted_card.card_id))
            return

        deleted_card.delete()

    except Exception as e:
        logger.exception(e)

    return HttpResponseRedirect(reverse('payment:view-cards'))
