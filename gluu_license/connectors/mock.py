import random
from hashlib import sha1 as sha_constructor
import datetime
from django.utils import timezone


def mock_license():

    return {'license_id': '0334bbcb-4121-4e23-a279-{}'.format(sha_constructor(str(random.random())).hexdigest()[:12]),
            'license_password': 'wkiNsOScQ0VjPJucI1go',
            'public_password': 'HaWakhnYWKONWcz84t1i',
            'public_key': 'ZwBd+OmGkTNQXlbx64jm+jDFODShWF+Ya+jHGzrI/nZBF/Hogn1t3ihbZQu65Fcvh21+mWtvPmWkGh4MeOTsnq+CINjCXiomERcUgPMR1UaxHV488vfrn0LOoc/8sZ7tbe5C99iOQJR7tQAQxaK8lwKEhJfwJBbPemgSZpm7mZWkWX1/NZTNnEJonHu++h1J1wD8t6APasYMIxBxOo8srC3MgStdMIHZfcwfo6Q+uKCAW7W7imAGUHBvVl6lkZrq61Qef4T81IhD3UmsfVsy3qUIBCIHj26UNKExqs6W0Uuk8MKPG8UFpAurYmIIMcbpw2bPk3iF2fg7oLlMRDSSQPdZGBwITM9fhlQ1y0Bg8SaVFClMUu1FoPETrRiuVgPJQ55vkl/FbrAGrgApEh7tUQ==',
            'expiration_date': timezone.now(),
            'creation_date': timezone.now() + datetime.timedelta(days=365)}


def mock_license_records():

    return {"monthly_statistic": {
            "2016-10": {
                "license_generated_count": 51,
                "mac_address": {"unknown": 29, "00-50-56-C0-00-08": 22}
            },
            "2016-11": {
                "license_generated_count": 28,
                "mac_address": {
                    "4C-BB-58-2C-B4-0F": 3,
                    "unknown": 17,
                    "00-50-56-C0-00-08": 8
                }
            },
            "2016-9": {
                "license_generated_count": 2,
                "mac_address": {"00-50-56-C0-00-08": 2}
            }},
            "total_generated_licenses": 64}


def mock_active_installations():

    return ["4C-BB-58-2C-B4-0F", "unknown", "00-50-56-C0-00-08", "4C-BB-58-2C-B4-0F", "unknown", "00-50-56-C0-00-08", "4C-BB-58-2C-B4-0F", "unknown", "00-50-56-C0-00-08", "4C-BB-58-2C-B4-0F", "unknown", "00-50-56-C0-00-08"]
