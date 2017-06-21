import json
import requests
import datetime
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from gluu_license.utils import get_time_frame
from gluu_license.models import LicenseRecord
from gluu_license.connectors import mock
from gluu_license.constants import ACTIVE_HOURS
from gluu_ecommerce.connectors.uma_access import obtain_authorized_rpt_token

logger = logging.getLogger('django')

# https://ox.gluu.org/doku.php?id=oxlicense:home

CREATE_LICENSE_ENDPOINT = 'https://license.gluu.org/oxLicense/rest/generateLicenseId/{}'
LICENSE_METADATA_ENDPOINT = 'https://license.gluu.org/oxLicense/rest/metadata'
LICENSE_STATISTICS_ENDPOINT = 'https://license.gluu.org/oxLicense/rest/statistic/monthly?licenseId={}'
LICENSE_STATISTICS_HOURLY_ENDPOINT = 'https://license.gluu.org/oxLicense/rest/statistic/lastHours'


def time_in_milliseconds(date_time):
    return int(date_time.strftime('%s')) * 1000


def acquire_license(license_name, number_licenses=1):

    if settings.MOCK_LICENSE:
        return mock.mock_license()

    url = CREATE_LICENSE_ENDPOINT.format(number_licenses)

    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers)

    if response.status_code != 403:

        logger.error('Failed to obtain ticket for UMA Authentication: {}, ({})'.format(
            response.text, response.status_code))
        return

    else:
        ticket = response.json()['ticket']

    rpt = obtain_authorized_rpt_token(ticket=ticket)

    headers['Authorization'] = 'Bearer {}'.format(rpt)

    creation_date = timezone.now()
    expiration_date = timezone.now() + datetime.timedelta(days=365)

    payload = {
        'active': True,
        'product': 'oxd',
        'license_name': license_name,
        'customer_name': license_name,
        'creation_date': time_in_milliseconds(creation_date),
        'expiration_date': time_in_milliseconds(expiration_date),
        'license_count_limit': 9999
    }

    response = requests.post(
        url,
        data=json.dumps(payload),
        headers=headers
    )

    if response.status_code != 200:
        logger.error('Error creating license: {} {}'.format(response.status_code, response.text))
        return

    else:
        license = response.json()[0]
        license['creation_date'] = creation_date
        license['expiration_date'] = expiration_date
        return license


def update_license_status(license):

    if settings.MOCK_LICENSE:
        return

    headers = {'Content-Type': 'application/json'}

    response = requests.put(
        LICENSE_METADATA_ENDPOINT,
        headers=headers
    )

    if response.status_code != 403:

        logger.error('Failed to obtain ticket for UMA Authentication: {}, ({})'.format(
            response.text, response.status_code))

        return

    else:
        ticket = response.json()['ticket']

    rpt = obtain_authorized_rpt_token(ticket=ticket)

    headers['Authorization'] = 'Bearer {}'.format(rpt)

    payload = {
        'active': license.is_active,
        'license_id': license.license_id,
        # unchanged data that must be sent back as it is
        'product': 'oxd',
        'license_name': license.account.get_name(),
        'license_count_limit': 9999,
        'creation_date': time_in_milliseconds(license.creation_date),
        'expiration_date': time_in_milliseconds(license.expiration_date)
    }

    response = requests.put(
        LICENSE_METADATA_ENDPOINT,
        data=json.dumps(payload),
        headers=headers
    )

    if response.status_code != 200:
        logger.error('Error updating license: {} {}'.format(
            license.license_id, response.status_code, response.text))

    return


def retrieve_usage_records(license_id):

    if settings.MOCK_LICENSE:
        return mock.mock_license_records()

    response = requests.get(LICENSE_STATISTICS_ENDPOINT.format(license_id))

    if response.status_code != 200:

        logger.error('Error retrieving active installation: {} {}'.format(
            response.status_code, response.text))

        return

    return response.json()


def retrieve_active_installations(license_id):

    if settings.MOCK_LICENSE:
        return mock.mock_active_installations()

    payload = {
        'licenseId': license_id,
        'hours': ACTIVE_HOURS
    }

    response = requests.get(
        LICENSE_STATISTICS_HOURLY_ENDPOINT.format(license_id), params=payload)

    if response.status_code != 200:

        logger.error('Error retrieving active installation: {} {}'.format(
            response.status_code, response.text))

        return

    return response.json().get('statistic').keys()


def sync_usage_records(license):

    raw_usage_records = retrieve_usage_records(license.license_id)

    if not raw_usage_records:
        return

    for time_frame, remote_record in raw_usage_records['monthly_statistic'].iteritems():

        year, month = get_time_frame(time_frame)

        try:

            record = LicenseRecord.objects.get(license=license, year=year, month=month)

            record.number_licenses = remote_record['license_generated_count']
            record.details = remote_record['mac_address']
            record.save()

        except ObjectDoesNotExist:

            record = LicenseRecord(
                license=license,
                month=month,
                year=year,
                number_licenses=remote_record['license_generated_count'],
                details=remote_record['mac_address']
            )

            record.save()


def get_usage_records(license):

    try:
        sync_usage_records(license)
        return LicenseRecord.objects.filter(license=license).order_by('-year', '-month')

    except (KeyError, TypeError) as e:
        logger.exception(e)
