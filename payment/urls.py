from django.conf.urls import url

from payment import views

urlpatterns = [
    url(
        r'^primary_card/$',
        views.get_primary_card_details,
        name='primary-card'
    ),
    url(
        r'^view/$',
        views.view_cards,
        name='view-cards'
    ),
    url(
        r'^add/$',
        views.add_card,
        name='add-card'
    ),
    url(
        r'^primary/(?P<card_id>\d+)/$',
        views.make_primary_card,
        name='primary-card'
    ),
    url(
        r'^delete/(?P<card_id>\d+)/$',
        views.delete_card,
        name='delete-card'
    )
]
