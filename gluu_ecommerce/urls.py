from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView
from django.conf import settings


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(
        r'^$',
        TemplateView.as_view(template_name='home.html'),
        name='home'
    ),
    url(
        r'^favicon\.ico$',
        RedirectView.as_view(url=settings.STATIC_URL + 'img/favicon.png')
    ),
    url(
        r'^docs$',
        RedirectView.as_view(url='/docs/')
    ),
    url(
        r'^account/',
        include('account.urls', namespace='account'),
    ),
    url(
        r'^payment/',
        include('payment.urls', namespace='payment'),
    ),
    url(
        r'^license/',
        include('gluu_license.urls', namespace='license'),
    ),
    url(
        '',
        include('social.apps.django_app.urls', namespace='social')
    )
]

handler404 = 'gluu_ecommerce.views.handle_404'
handler500 = 'gluu_ecommerce.views.handle_500'
