import logging
import requests

from django.conf import settings
from social.backends.oauth import BaseOAuth2

from account.connectors.idp_interface import get_user

GLUU_OAUTH2_SCOPE = ['openid', 'email', 'profile']
GLUU_OAUTH2_SERVER = 'seed.gluu.org'
GLUUAPIS_PROFILE = 'https://idp.gluu.org/oxauth/seam/resource/restv1/oxauth/userinfo'
GLUUAPIS_EMAIL = 'email'

logger = logging.getLogger('django')


class GluuOAuth2Backend(BaseOAuth2):

    name = 'gluu'

    AUTHORIZATION_URL = 'https://idp.gluu.org/oxauth/seam/resource/restv1/oxauth/authorize'
    ACCESS_TOKEN_URL = 'https://idp.gluu.org/oxauth/seam/resource/restv1/oxauth/token'

    RESPONSE_TYPE = 'code'
    REDIRECT_STATE = False
    STATE_PARAMETER = True
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['openid', 'email', 'profile', 'user_name', 'clientinfo']

    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires'),
        ('id_token', 'id_token', True),
        ('session_state', 'session_state', True),
        ('access_type', 'access_type', True)
    ]

    def get_user_id(self, details, response):

        user_id = details['email']
        return user_id

    def get_user_details(self, response):

        return {'username': response.get('user_name', ''),
                'email': response.get('email', ''),
                'fullname': response.get('name', ''),
                'first_name': response.get('given_name', ''),
                'last_name': response.get('family_name', ''),
                'idp_uuid': response.get('inum', '')}

    def user_data(self, access_token, *args, **kwargs):

        self.strategy.session_set('gluu_state', self.data['state'])

        self.strategy.session_set('gluu_session', self.data['session_state'])

        self.strategy.session_set('gluu_code', self.data['code'])

        return gluuapis_profile(GLUUAPIS_PROFILE, access_token)


def gluuapis_profile(url, access_token):

    data = {'access_token': access_token, 'alt': 'json'}

    r = requests.get(url, params=data, verify=settings.VERIFY_SSL)

    if r.status_code == requests.codes.ok:
        return r.json()

    return None


def sync_phone_number(strategy, is_new, user, *args, **kwargs):

    try:

        if not user.phone_number:
            user.phone_number = get_user(user)['phoneNumbers'][0]['value']
            user.save()

    except (KeyError, AttributeError, IndexError) as e:
        logger.info('{} doesn\'t have a phone number'.format(user.email))

    except Exception as e:
        logger.exception(e)
