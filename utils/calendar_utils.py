"""
Utility functions for working with dates and calendars
"""
from datetime import date, datetime, timedelta
import calendar
from typing import List, Dict, Any, Optional, Tuple, Union

def get_month_calendar(year: int, month: int) -> List[List[Union[int, None]]]:
    """
    Generate a calendar matrix for the specified month
    
    Returns a list of weeks, each week being a list of days
    (None for days that are not part of the month)
    """
    cal = calendar.monthcalendar(year, month)
    return cal

def get_month_name(month: int) -> str:
    """Return the name of the month"""
    return calendar.month_name[month]

def get_next_month(year: int, month: int) -> Tuple[int, int]:
    """Return the year and month of the next month"""
    if month == 12:
        return year + 1, 1
    return year, month + 1

def get_prev_month(year: int, month: int) -> Tuple[int, int]:
    """Return the year and month of the previous month"""
    if month == 1:
        return year - 1, 12
    return year, month - 1

def get_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generate a list of dates between start_date and end_date (inclusive)
    """
    delta = (end_date - start_date).days
    return [start_date + timedelta(days=i) for i in range(delta + 1)]

def is_date_in_range(test_date: date, start_date: date, end_date: date) -> bool:
    """
    Check if a date is within a date range (inclusive)
    """
    return start_date <= test_date <= end_date

def get_days_in_month(year: int, month: int) -> int:
    """
    Return the number of days in a month
    """
    return calendar.monthrange(year, month)[1]

def get_calendar_with_availability(
    year: int, 
    month: int, 
    unavailable_dates: List[str]
) -> Dict[str, Any]:
    """
    Generate a calendar dictionary with availability information
    
    Args:
        year: Calendar year
        month: Calendar month
        unavailable_dates: List of unavailable dates in ISO format (YYYY-MM-DD)
    
    Returns:
        Dictionary with calendar information including:
        - month_name: Name of the month
        - year: Year
        - month: Month number
        - prev_month: (year, month) tuple for previous month
        - next_month: (year, month) tuple for next month
        - calendar: List of weeks, each week being a list of day dictionaries
          Each day dictionary has:
          - day: Day number (or None for padding days)
          - date: ISO formatted date
          - available: Whether the date is available
    """
    # Convert string dates to date objects
    unavailable_date_objs = [
        date.fromisoformat(date_str) for date_str in unavailable_dates
    ]
    
    # Get calendar matrix
    cal_matrix = get_month_calendar(year, month)
    
    # Build detailed calendar
    calendar_data = []
    for week in cal_matrix:
        week_data = []
        for day in week:
            if day == 0:  # Padding day
                week_data.append({
                    'day': None,
                    'date': None,
                    'available': None
                })
            else:
                current_date = date(year, month, day)
                date_str = current_date.isoformat()
                week_data.append({
                    'day': day,
                    'date': date_str,
                    'available': current_date not in unavailable_date_objs
                })
        calendar_data.append(week_data)
    
    # Get previous and next month
    prev_month = get_prev_month(year, month)
    next_month = get_next_month(year, month)
    
    return {
        'month_name': get_month_name(month),
        'year': year,
        'month': month,
        'prev_month': prev_month,
        'next_month': next_month,
        'calendar': calendar_data
    }

def get_multiple_months_calendar(
    start_year: int,
    start_month: int,
    num_months: int,
    unavailable_dates: List[str]
) -> List[Dict[str, Any]]:
    """
    Generate calendar data for multiple months
    
    Args:
        start_year: Starting year
        start_month: Starting month
        num_months: Number of months to generate
        unavailable_dates: List of unavailable dates in ISO format
    
    Returns:
        List of calendar dictionaries, one for each month
    """
    calendars = []
    current_year, current_month = start_year, start_month
    
    for _ in range(num_months):
        cal_data = get_calendar_with_availability(
            current_year, current_month, unavailable_dates
        )
        calendars.append(cal_data)
        
        # Move to next month
        current_year, current_month = get_next_month(current_year, current_month)
    
    return calendars

def parse_date_or_today(date_str: Optional[str] = None) -> date:
    """
    Parse a date string in ISO format (YYYY-MM-DD) or return today's date
    """
    if date_str:
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            pass
    return date.today()
