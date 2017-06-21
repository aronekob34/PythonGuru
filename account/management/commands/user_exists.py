from django.core.management.base import BaseCommand

from account.connectors.idp_interface import email_exists


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument('-email', required=True)

    def handle(self, *args, **options):

        email = options['email']

        if email_exists(email):
            return 'Found'

        return 'Not found'
