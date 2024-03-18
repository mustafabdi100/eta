document.getElementById('howToApplyCard').addEventListener('click', function() {
    document.getElementById('applicationPopup').classList.add('modal-active');
});

document.querySelector('.close').addEventListener('click', function() {
    document.getElementById('applicationPopup').classList.remove('modal-active');
});

document.getElementById('faqsCard').addEventListener('click', function() {
    document.getElementById('faqsPopup').classList.add('modal-active');
});

document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', function() {
        this.parentElement.parentElement.classList.remove('modal-active');
    });
});

const checkApplicationBtn = document.getElementById('checkApplicationBtn');
const applicationModal = document.getElementById('applicationModal');
const closeModal = document.getElementById('closeModal');
const closeBtn = document.getElementById('closeBtn');

// Open modal event
checkApplicationBtn.addEventListener('click', function() {
    applicationModal.classList.add('modal-active');
});

// Close modal events
closeModal.addEventListener('click', function() {
    applicationModal.classList.remove('modal-active');
});
closeBtn.addEventListener('click', function() {
    applicationModal.classList.remove('modal-active');
});

// Also close on click outside of the modal
window.addEventListener('click', function(e) {
    if (e.target === applicationModal) {
        applicationModal.classList.remove('modal-active');
    }
});
// Get the form element
const form = document.getElementById('search-form');

// Add an event listener for form submission
form.addEventListener('submit', function(event) {
    // Get the values of the input fields
    const businessName = document.getElementById('businessName').value.trim();
    const referenceNumber = document.getElementById('referenceNumber').value.trim();

    // Check if at least one field is filled out
    if (!businessName && !referenceNumber) {
        // If both fields are empty, prevent form submission
        event.preventDefault();
        alert('Please enter either the Business Name or Reference Number.');
    }
});

