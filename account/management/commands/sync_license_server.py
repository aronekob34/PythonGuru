import logging

from django.core.management.base import BaseCommand

from account.models import Account
from gluu_license.connectors.license_interface import sync_usage_records
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger('billing')

class Command(BaseCommand):


    def handle(self, *args, **options):

        accounts = Account.objects.all()

        for account in accounts:

            try:

                sync_usage_records(account.license)

            except ObjectDoesNotExist:

                logger.error('Failed to sync usage records for account: {}'.format(account))
