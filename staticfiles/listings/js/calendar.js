function calendar() {
    return {
        currentYear: new Date().getFullYear(),
        currentMonth: new Date().getMonth(),
        unavailableDates: [],

        init() {
            console.log('Calendar component initialized');
            // Parse unavailable dates from global variable if it exists
            if (window.unavailableDatesJson) {
                this.unavailableDates = JSON.parse(window.unavailableDatesJson);
            }
            this.generateCalendar();
        },

        get currentMonthName() {
            const months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            return months[this.currentMonth];
        },

        get calendarDays() {
            return this.generateCalendar();
        },

        generateCalendar() {
            const firstDay = new Date(this.currentYear, this.currentMonth, 1);
            const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0);
            const startDate = new Date(firstDay);
            startDate.setDate(startDate.getDate() - firstDay.getDay());

            const weeks = [];
            let currentDate = new Date(startDate);

            for (let week = 0; week < 6; week++) {
                const weekDays = [];

                for (let day = 0; day < 7; day++) {
                    const dateStr = currentDate.toISOString().split('T')[0];
                    const isCurrentMonth = currentDate.getMonth() === this.currentMonth;
                    const isToday = this.isToday(currentDate);
                    const isUnavailable = this.unavailableDates.includes(dateStr);

                    weekDays.push({
                        date: isCurrentMonth ? dateStr : null,
                        dayNumber: isCurrentMonth ? currentDate.getDate() : null,
                        isToday: isToday,
                        isUnavailable: isUnavailable,
                        isCurrentMonth: isCurrentMonth
                    });

                    currentDate.setDate(currentDate.getDate() + 1);
                }

                weeks.push(weekDays);

                // Stop if we've gone past the current month and filled a complete week
                if (currentDate.getMonth() !== this.currentMonth && week > 3) {
                    break;
                }
            }

            return weeks;
        },

        isToday(date) {
            const today = new Date();
            return date.toDateString() === today.toDateString();
        },

        previousMonth() {
            if (this.currentMonth === 0) {
                this.currentMonth = 11;
                this.currentYear--;
            } else {
                this.currentMonth--;
            }
        },

        nextMonth() {
            if (this.currentMonth === 11) {
                this.currentMonth = 0;
                this.currentYear++;
            } else {
                this.currentMonth++;
            }
        },

        selectDate(date) {
            if (!date) return;
            console.log('Selected date:', date);
            // You can add date selection logic here
        }
    };
}

// Initialize calendar function for legacy code compatibility
function initCalendar(unavailableDates) {
    console.log('Legacy initCalendar called with:', unavailableDates);
    window.unavailableDatesJson = JSON.stringify(unavailableDates || []);
}