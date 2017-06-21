$(function(){

  //Set placeholders
  if ($('#id_country').children().length > 0) {
    $('#id_country').children()[0].innerHTML = 'Country';
  }

  $('#id_first_name').attr('placeholder', 'First Name');
  $('#id_last_name').attr('placeholder', 'Last Name');
  $('#id_email').attr('placeholder', 'Email');
  $('#id_phone_number').attr('placeholder', 'Phone Number');
  $('#id_password1').attr('placeholder', 'Select a password');
  $('#id_password2').attr('placeholder', 'Confirm your password');

  $('#id_business_name').attr('placeholder', 'Business Name');
  // $('#id_name').attr('placeholder', 'Name');
  $('input[name="name"]').attr('readonly', 'readonly');
  $('#id_address_1').attr('placeholder', 'Address Line 1');
  $('#id_address_2').attr('placeholder', 'Address Line 2');
  $('#id_city').attr('placeholder', 'City');
  if ($('#id_state').children().length > 0) {
    $('#id_state').children()[0].innerHTML = 'State';
  }
  $('#id_zip_code').attr('placeholder', 'Zip Code');

  //Show or hide inputs based on account type
  if($('select[name="account-type"]').val() == 'biz') {
    $('#id_business_name').attr('required', 'required');
  }

  $('select[name="account-type"]').change(function(){
    if($(this).val() == 'ind') {
      $('#id_business_name').parent().parent().slideUp();
      $('#id_business_name').removeAttr('required');
    } else {
      $('#id_business_name').parent().parent().slideDown();
      $('#id_business_name').attr('required', 'required');
    }
  });

  // Style error boxes
  // $('.errorlist').parent().parent().parent().find('input').addClass('error');
  // $('.errorlist').parent().parent().siblings('div').find('input').each(function(index, item){
  //   $(item).change(function(){
  //     $(item).removeClass('error');
  //     $(item).parent().parent().find('.errorlist').slideUp();
  //   });
  // });

  // Show State for country US
  if ($('#id_country').val() === 'US'){
    $('.form-group.state-zip').slideDown();
  }
  $('#id_country').change(function(){
    if ($(this).val() === 'US') {
      $('.form-group.state-zip').slideDown();
      $('#id_zip_code').attr('required', 'required');
      $('#id_state').attr('required', 'required');
    } else {
      $('.form-group.state-zip').slideUp();
      $('#id_zip_code').removeAttr('required').val('');
      $('#id_state').removeAttr('required').val('');
    }
  });
});
