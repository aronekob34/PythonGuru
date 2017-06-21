import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django.http import HttpResponseServerError, HttpResponseRedirect

from gluu_license import models
from gluu_license.connectors import license_interface

logger = logging.getLogger('django')


@login_required
def activate_license(request, license_id):

    try:

        license = models.License.objects.get(license_id=license_id)

        if license.is_active:
            license.is_active = False
        elif not license.is_blocked:
            license.is_active = True
        else:
            messages.error(request, 'Your oxd license has been deactivated and all oxd installations associated with this license will not work until the balance is cleared. In order to complete your payment and reactivate your oxd license, please reach out to will@gluu.org.')
            return HttpResponseRedirect(reverse('account:dashboard'))

        license_interface.update_license_status(license)
        license.save()

        return HttpResponseRedirect(reverse('account:dashboard'))

    except Exception as e:
        logger.error(e)
        return HttpResponseServerError(e)
