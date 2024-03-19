$(document).ready(function() {
    var contactForms = $('.contact-form');
    var addContactButton = $('#add-contact');

    contactForms.not(':first').hide();

    addContactButton.click(function() {
        var visibleForm = contactForms.filter(':visible');
        var nextForm = visibleForm.next('.contact-form');

        if (nextForm.length) {
            visibleForm.find('.accordion-header').addClass('active');
            visibleForm.find('.accordion-content').show();
            visibleForm.wrap('<div class="accordion"></div>');
            nextForm.show().find('.accordion-header').trigger('click');
        } else {
            addContactButton.prop('disabled', true);
        }
    });

    $(document).on('click', '.contact-form .accordion-header', function() {
        var accordionContent = $(this).next('.accordion-content');
        if (!$(this).hasClass('active')) {
            contactForms.find('.accordion-content').not(accordionContent).slideUp();
            contactForms.find('.accordion-header').not(this).removeClass('active');
            $(this).addClass('active');
            accordionContent.slideDown();
        } else {
            $(this).removeClass('active');
            accordionContent.slideUp();
        }
    });

    $('form').submit(function(e) {
        var requiredFields = $('#contact-form-1').find('input[required]');
        var emptyRequiredFields = requiredFields.filter(function() {
            return $(this).val().trim() === '';
        });
        if (emptyRequiredFields.length > 0) {
            e.preventDefault();
            alert('Please fill in all the required fields for Contact 1.');
        } else {
            var invalidOptionalForm = false;
            contactForms.not(':first').each(function() {
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
                alert('Please fill in all fields for the optional contacts or leave them empty.');
            }
        }
    });
});