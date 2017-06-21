jQuery.fn.selectText = function(){
    var doc = document
        , element = this[0]
        , range, selection
    ;
    if (doc.body.createTextRange) {
        range = document.body.createTextRange();
        range.moveToElementText(element);
        range.select();
    } else if (window.getSelection) {
        selection = window.getSelection();
        range = document.createRange();
        range.selectNodeContents(element);
        selection.removeAllRanges();
        selection.addRange(range);
    }
};

$(document).ready(function () {
	"use strict"; // start of use strict

	/*==============================
	Preloader
	==============================*/
	$(window).load(function(){
		$('body').imagesLoaded(function(){
			$('.preloader').fadeOut();
		});
	});

	/*==============================
	Mobile navigation
	==============================*/
	$('.navigation-button').on('click', function() {
		$(this).toggleClass('active');
		$('.mobile-navigation').toggleClass('active');
	});

	/*==============================
	Navigation dropdown
	==============================*/
	$('.desktop-navigation .dropdown').hover(
		function() {
			$('.dropdown-menu', this).not('.in .dropdown-menu').stop(true, true);
			$(this).toggleClass('open');
		},
		function() {
			$('.dropdown-menu', this).not('.in .dropdown-menu').stop(true, true);
			$(this).toggleClass('open');
	});

	/*==============================
	Filter
	==============================*/
	$('.filter__search input').on('click', function(){
		$('.filter__search').toggleClass('focus');
	});
	$(document).on('click', function(e) {
		if (!$(e.target).closest('.filter__search.focus').length) {
			$('.filter__search').removeClass('focus');
		}
		e.stopPropagation();
	});

	/*==============================
	Back to top
	==============================*/
	$('.back-to-top').on('click', function() {
		$('body,html').animate({
			scrollTop: 0 ,
			}, 700 // - duration of the top scrolling animation (in ms)
		);
	});

	//Pre selectors and copy
	$('pre, code').click(function(e){
		$(this).selectText();
	});

	new Clipboard('.copy-pre');

  $('[data-toggle="tooltip"]').tooltip();

});
