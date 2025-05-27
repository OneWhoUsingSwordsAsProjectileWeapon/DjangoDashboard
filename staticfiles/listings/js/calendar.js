/**
 * Calendar functionality for listing availability
 */

function initCalendar(unavailableDates) {
    // Set up date inputs
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');
    
    if (checkInInput && checkOutInput) {
        setupDateConstraints(checkInInput, checkOutInput, unavailableDates);
        setupDateChangeHandlers(checkInInput, checkOutInput, unavailableDates);
    }
}

/**
 * Set minimum dates and other constraints on date inputs
 */
function setupDateConstraints(checkInInput, checkOutInput, unavailableDates) {
    // Set min date to today
    const today = new Date();
    const todayFormatted = formatDateForInput(today);
    
    checkInInput.min = todayFormatted;
    checkOutInput.min = todayFormatted;
    
    // Set initial values if provided in URL
    const urlParams = new URLSearchParams(window.location.search);
    const checkInParam = urlParams.get('check_in');
    const checkOutParam = urlParams.get('check_out');
    
    if (checkInParam && isValidDate(checkInParam)) {
        checkInInput.value = checkInParam;
        
        // Set min checkout date to day after checkin
        const checkInDate = new Date(checkInParam);
        checkInDate.setDate(checkInDate.getDate() + 1);
        checkOutInput.min = formatDateForInput(checkInDate);
    }
    
    if (checkOutParam && isValidDate(checkOutParam)) {
        checkOutInput.value = checkOutParam;
    }
}

/**
 * Set up event handlers for date changes
 */
function setupDateChangeHandlers(checkInInput, checkOutInput, unavailableDates) {
    // When check-in date changes
    checkInInput.addEventListener('change', function() {
        if (!this.value) return;
        
        const checkInDate = new Date(this.value);
        
        // Set min checkout date to day after checkin
        checkInDate.setDate(checkInDate.getDate() + 1);
        checkOutInput.min = formatDateForInput(checkInDate);
        
        // Clear checkout date if it's before new check-in date
        if (checkOutInput.value && new Date(checkOutInput.value) <= new Date(this.value)) {
            checkOutInput.value = '';
        }
        
        // Check if the selected date is unavailable
        if (isDateUnavailable(this.value, unavailableDates)) {
            showUnavailableAlert(checkInInput);
            this.value = '';
        } else {
            // If checkout is already selected, validate the range
            if (checkOutInput.value) {
                validateDateRange(this.value, checkOutInput.value, unavailableDates);
            }
        }
        
        // Update pricing if both dates are selected
        if (checkOutInput.value) {
            triggerPriceUpdate();
        }
    });
    
    // When check-out date changes
    checkOutInput.addEventListener('change', function() {
        if (!this.value || !checkInInput.value) return;
        
        // Check if the selected date is unavailable
        if (isDateUnavailable(this.value, unavailableDates)) {
            showUnavailableAlert(checkOutInput);
            this.value = '';
        } else {
            // Validate the date range
            validateDateRange(checkInInput.value, this.value, unavailableDates);
        }
        
        // Update pricing
        triggerPriceUpdate();
    });
}

/**
 * Validate that a date range doesn't contain unavailable dates
 */
function validateDateRange(startDateStr, endDateStr, unavailableDates) {
    const startDate = new Date(startDateStr);
    const endDate = new Date(endDateStr);
    
    // Check each date in the range
    let currentDate = new Date(startDate);
    while (currentDate <= endDate) {
        const dateStr = formatDateForInput(currentDate);
        if (isDateUnavailable(dateStr, unavailableDates)) {
            // Show alert about unavailable dates in range
            alert('Your date range includes unavailable dates. Please select a different range.');
            return false;
        }
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return true;
}

/**
 * Check if a date is unavailable
 */
function isDateUnavailable(dateStr, unavailableDates) {
    return unavailableDates.includes(dateStr);
}

/**
 * Format a Date object as YYYY-MM-DD for input elements
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Check if a string is a valid date in format YYYY-MM-DD
 */
function isValidDate(dateStr) {
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(dateStr)) return false;
    
    const date = new Date(dateStr);
    return date instanceof Date && !isNaN(date);
}

/**
 * Show an alert for unavailable date selection
 */
function showUnavailableAlert(inputElement) {
    // Create and show alert
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-danger mt-2';
    alertElement.textContent = 'This date is unavailable. Please select another date.';
    
    // Insert alert after the input
    inputElement.parentNode.appendChild(alertElement);
    
    // Remove alert after 3 seconds
    setTimeout(() => {
        alertElement.remove();
    }, 3000);
}

/**
 * Trigger price update using HTMX
 */
function triggerPriceUpdate() {
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm && typeof htmx !== 'undefined') {
        htmx.trigger(bookingForm, 'update-price');
    }
}

/**
 * Set date inputs based on selected dates
 */
function setDateInputs(checkInDate, checkOutDate) {
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');
    
    if (checkInInput && checkInDate) {
        checkInInput.value = checkInDate;
        checkInInput.dispatchEvent(new Event('change'));
    }
    
    if (checkOutInput && checkOutDate) {
        checkOutInput.value = checkOutDate;
        checkOutInput.dispatchEvent(new Event('change'));
    }
}
