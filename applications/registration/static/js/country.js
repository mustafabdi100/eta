document.getElementById('id_country').addEventListener('change', function() {
    var countrySelect = this;
    var citySelect = document.getElementById('id_city');
    var selectedCountry = countrySelect.value;

    // Clear existing city options
    citySelect.innerHTML = '<option value="">Select a city</option>';

    if (selectedCountry) {
        // Make an AJAX request to get the cities for the selected country
        fetch(`/get-cities/${selectedCountry}/`)
            .then(response => response.json())
            .then(cities => {
                // Populate the city options
                cities.forEach(city => {
                    var option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
            });
    }
});