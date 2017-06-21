from django.conf.urls import url

from gluu_license import views

urlpatterns = [
    url(
        r'^activate_license/(?P<license_id>[\w\-]+)/$',
        views.activate_license,
        name='activate'
    )
]
