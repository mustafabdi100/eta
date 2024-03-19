$(document).ready(function() {
    var creditCardForms = $('.credit-card-form');
    var addCreditCardButton = $('#add-credit-card');

    creditCardForms.not(':first').hide();

    addCreditCardButton.click(function() {
        var visibleForm = creditCardForms.filter(':visible');
        var nextForm = visibleForm.next('.credit-card-form');

        if (nextForm.length) {
            visibleForm.find('.accordion-header').addClass('active');
            visibleForm.find('.accordion-content').show();
            visibleForm.wrap('<div class="accordion"></div>');
            nextForm.show().find('.accordion-header').trigger('click');
        } else {
            addCreditCardButton.prop('disabled', true);
        }
    });

    $(document).on('click', '.credit-card-form .accordion-header', function() {
        var accordionContent = $(this).next('.accordion-content');
        if (!$(this).hasClass('active')) {
            creditCardForms.find('.accordion-content').not(accordionContent).slideUp();
            creditCardForms.find('.accordion-header').not(this).removeClass('active');
            $(this).addClass('active');
            accordionContent.slideDown();
        } else {
            $(this).removeClass('active');
            accordionContent.slideUp();
        }
    });

    $('form').submit(function(e) {
        var invalidOptionalForm = false;
        creditCardForms.each(function() {
            var form = $(this);
            var formFields = form.find('input[required], select[required]');
            var filledFields = formFields.filter(function() {
                return $(this).val().trim() !== '';
            });
            if (filledFields.length > 0 && filledFields.length !== formFields.length) {
                invalidOptionalForm = true;
                form.find('.accordion-header').trigger('click');
                return false;
            }
        });
        if (invalidOptionalForm) {
            e.preventDefault();
            alert('Please fill in all fields for the credit cards or leave them empty.');
        }
    });
});