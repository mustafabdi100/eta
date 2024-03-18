document.addEventListener('DOMContentLoaded', function() {
    var checkApplicationBtn = document.getElementById('checkApplicationBtn');
    var applicationModal = document.getElementById('applicationModal');
    var closeModal = document.getElementById('closeModal');
    var closeBtn = document.getElementById('closeBtn');
    var searchForm = document.getElementById('search-form');
    var statusPopup = document.getElementById('status-popup');

    checkApplicationBtn.addEventListener('click', function() {
        applicationModal.style.display = 'flex';
    });

    closeModal.addEventListener('click', function() {
        applicationModal.style.display = 'none';
        resetForm();
    });

    closeBtn.addEventListener('click', function() {
        applicationModal.style.display = 'none';
        resetForm();
    });

    searchForm.addEventListener('submit', function(event) {
        event.preventDefault();

        var formData = new FormData(searchForm);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', searchApplicationStatusUrl);
        xhr.setRequestHeader('X-CSRFToken', formData.get('csrfmiddlewaretoken'));
        xhr.onload = function() {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.applications) {
                    var application = response.applications[0];
                    var statusHtml = '<div class="bg-white rounded-lg shadow-lg p-6">' +
                        '<h2 class="text-2xl font-bold mb-4 text-center">Application Status</h2>' +
                        '<p class="text-xl font-semibold text-center ' + getStatusColor(application.status) + '">' +
                        'Your application status is ' + application.status +
                        '</p>' +
                        '<div class="flex justify-center mt-6">' +
                        '<button id="closeStatusPopup" class="px-4 py-2 bg-gray-800 text-white font-bold rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-700 focus:ring-opacity-50">' +
                        'Close' +
                        '</button>' +
                        '</div>' +
                        '</div>';
                    statusPopup.innerHTML = statusHtml;
                    statusPopup.style.display = 'block';
                    searchForm.style.display = 'none';

                    var closeStatusPopupBtn = document.getElementById('closeStatusPopup');
                    closeStatusPopupBtn.addEventListener('click', function() {
                        statusPopup.style.display = 'none';
                        applicationModal.style.display = 'none';
                        resetForm();
                    });
                } else if (response.error_message) {
                    var errorHtml = '<div class="bg-white rounded-lg shadow-lg p-6">' +
                        '<h2 class="text-2xl font-bold mb-4 text-center">No Application Found</h2>' +
                        '<p class="text-xl font-semibold text-center text-red-600">' + response.error_message + '</p>' +
                        '<div class="flex justify-center mt-6">' +
                        '<button id="closeErrorPopup" class="px-4 py-2 bg-gray-800 text-white font-bold rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-700 focus:ring-opacity-50">' +
                        'Close' +
                        '</button>' +
                        '</div>' +
                        '</div>';
                    statusPopup.innerHTML = errorHtml;
                    statusPopup.style.display = 'block';
                    searchForm.style.display = 'none';

                    var closeErrorPopupBtn = document.getElementById('closeErrorPopup');
                    closeErrorPopupBtn.addEventListener('click', function() {
                        statusPopup.style.display = 'none';
                        applicationModal.style.display = 'none';
                        resetForm();
                    });
                }
            }
        };
        xhr.send(formData);
    });

    function getStatusColor(status) {
        if (status === 'approved') {
            return 'text-green-600';
        } else if (status === 'pending') {
            return 'text-orange-500';
        } else {
            return 'text-red-600';
        }
    }

    function resetForm() {
        searchForm.reset();
        searchForm.style.display = 'block';
        statusPopup.style.display = 'none';
    }
});