$(document).ready(function(){

    var csrftoken = Cookies.get('csrftoken');

    $.ajax({
        type: 'GET',
        url: '/payment/primary_card/',
        data: 'csrfmiddlewaretoken=' + csrftoken
    }).done(function(card_details){

        additionalMarkup = '<ul><li>'+card_details['brand']+'</li>';
        additionalMarkup += '<li>'+card_details['last4']+'</li></ul>';
        $('#card-details').html(additionalMarkup);


    }).fail(function() {

    });
});
