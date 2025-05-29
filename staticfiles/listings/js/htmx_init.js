/**
 * Initialize HTMX enhancements for the listings functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltip content on hover elements
    initTooltips();
    
    // Set up real-time price calculation
    setupPriceCalculation();
    
    // Set up search form enhancements
    enhanceSearchForm();
    
    // Set up dynamic form validation
    setupFormValidation();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Set up real-time price calculation with HTMX
 */
function setupPriceCalculation() {
    // Add custom event for price updates
    htmx.on('#booking-form', 'update-price', function(event) {
        const formEl = event.target;
        htmx.trigger(formEl, 'change');
    });
    
    // Monitor for successful price calculations
    htmx.on('#pricing-container', 'htmx:afterSwap', function(event) {
        // If error message exists, highlight the date inputs
        if (event.detail.target.querySelector('.alert-danger')) {
            highlightDateInputs(true);
        } else {
            highlightDateInputs(false);
        }
    });
}

/**
 * Highlight date inputs to indicate errors
 */
function highlightDateInputs(hasError) {
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');
    
    if (checkInInput && checkOutInput) {
        if (hasError) {
            checkInInput.classList.add('is-invalid');
            checkOutInput.classList.add('is-invalid');
        } else {
            checkInInput.classList.remove('is-invalid');
            checkOutInput.classList.remove('is-invalid');
            
            // Add success class if both have values
            if (checkInInput.value && checkOutInput.value) {
                checkInInput.classList.add('is-valid');
                checkOutInput.classList.add('is-valid');
            }
        }
    }
}

/**
 * Enhance search form with dynamic UI updates
 */
function enhanceSearchForm() {
    // Add location suggestions as you type
    const locationInput = document.getElementById('location');
    if (locationInput) {
        locationInput.addEventListener('focus', function() {
            // Show popular locations
            const suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'location-suggestions card';
            suggestionsDiv.innerHTML = `
                <div class="card-body p-2">
                    <p class="small text-muted mb-2">Popular destinations:</p>
                    <div class="suggestion-chips">
                        <button type="button" class="btn btn-sm btn-outline-secondary me-1 mb-1" onclick="setLocation('Москва')">Москва</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary me-1 mb-1" onclick="setLocation('Санкт-Петербург')">Санкт-Петербург</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary me-1 mb-1" onclick="setLocation('Сочи')">Сочи</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary me-1 mb-1" onclick="setLocation('Казань')">Казань</button>
                    </div>
                </div>
            `;
            
            // Insert after input
            locationInput.parentNode.appendChild(suggestionsDiv);
            
            // Remove on blur
            locationInput.addEventListener('blur', function() {
                setTimeout(() => {
                    if (document.querySelector('.location-suggestions')) {
                        document.querySelector('.location-suggestions').remove();
                    }
                }, 200);
            });
        });
    }
}

/**
 * Set location input value
 */
function setLocation(location) {
    const locationInput = document.getElementById('location');
    if (locationInput) {
        locationInput.value = location;
        // Remove suggestions
        if (document.querySelector('.location-suggestions')) {
            document.querySelector('.location-suggestions').remove();
        }
    }
}

/**
 * Set up form validation
 */
function setupFormValidation() {
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(event) {
            const checkInInput = document.getElementById('check_in');
            const checkOutInput = document.getElementById('check_out');
            
            if (!checkInInput.value || !checkOutInput.value) {
                event.preventDefault();
                
                // Show validation error
                const alertMsg = document.createElement('div');
                alertMsg.className = 'alert alert-danger mt-3';
                alertMsg.textContent = 'Please select both check-in and check-out dates';
                
                if (!document.querySelector('#booking-form .alert')) {
                    bookingForm.appendChild(alertMsg);
                    
                    // Remove after 3 seconds
                    setTimeout(() => {
                        alertMsg.remove();
                    }, 3000);
                }
                
                // Highlight inputs
                if (!checkInInput.value) checkInInput.classList.add('is-invalid');
                if (!checkOutInput.value) checkOutInput.classList.add('is-invalid');
            }
        });
    }
}
