"""
Utility functions for calculating prices
"""
from decimal import Decimal
from typing import Dict, Union, List, Tuple
from datetime import date, timedelta

def calculate_night_price(
    base_price: Decimal, 
    date_obj: date,
    seasonal_adjustments: Dict[str, Decimal] = None,
    day_of_week_adjustments: Dict[int, Decimal] = None
) -> Decimal:
    """
    Calculate the price for a specific night, accounting for seasonal and day-of-week adjustments
    
    Args:
        base_price: Base price per night
        date_obj: Date object for the night
        seasonal_adjustments: Dictionary mapping ISO formatted date ranges ('YYYY-MM-DD:YYYY-MM-DD') 
                              to price multipliers
        day_of_week_adjustments: Dictionary mapping day of week (0=Monday, 6=Sunday) to price multipliers
    
    Returns:
        Adjusted price for the night
    """
    price = base_price
    
    # Apply seasonal adjustments if provided
    if seasonal_adjustments:
        # Check if date falls within any seasonal adjustment period
        for date_range, multiplier in seasonal_adjustments.items():
            start_str, end_str = date_range.split(':')
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
            
            if start_date <= date_obj <= end_date:
                price = price * multiplier
                break
    
    # Apply day of week adjustments if provided
    if day_of_week_adjustments:
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = date_obj.weekday()
        
        if day_of_week in day_of_week_adjustments:
            price = price * day_of_week_adjustments[day_of_week]
    
    return price

def calculate_stay_price(
    base_price: Decimal,
    start_date: date,
    end_date: date,
    cleaning_fee: Decimal = Decimal('0'),
    service_fee: Decimal = Decimal('0'),
    seasonal_adjustments: Dict[str, Decimal] = None,
    day_of_week_adjustments: Dict[int, Decimal] = None,
    length_of_stay_discount: Dict[int, Decimal] = None
) -> Dict[str, Decimal]:
    """
    Calculate the total price for a stay
    
    Args:
        base_price: Base price per night
        start_date: Check-in date
        end_date: Check-out date
        cleaning_fee: One-time cleaning fee
        service_fee: One-time service fee
        seasonal_adjustments: Dictionary mapping date ranges to price multipliers
        day_of_week_adjustments: Dictionary mapping day of week to price multipliers
        length_of_stay_discount: Dictionary mapping minimum nights to discount multipliers
    
    Returns:
        Dictionary containing:
        - 'base_total': Total base price for all nights
        - 'nightly_prices': List of tuples (date, price) for each night
        - 'cleaning_fee': Cleaning fee
        - 'service_fee': Service fee
        - 'discount': Discount amount (if any)
        - 'total': Final total price
        - 'nights': Number of nights
    """
    # Calculate number of nights
    nights = (end_date - start_date).days
    
    if nights <= 0:
        raise ValueError("End date must be after start date")
    
    # Calculate price for each night
    nightly_prices = []
    current_date = start_date
    
    while current_date < end_date:
        night_price = calculate_night_price(
            base_price, 
            current_date,
            seasonal_adjustments,
            day_of_week_adjustments
        )
        nightly_prices.append((current_date, night_price))
        current_date += timedelta(days=1)
    
    # Calculate base total
    base_total = sum(price for _, price in nightly_prices)
    
    # Apply length of stay discount if applicable
    discount = Decimal('0')
    if length_of_stay_discount:
        # Find the applicable discount
        applicable_discount = None
        for min_nights, discount_multiplier in sorted(length_of_stay_discount.items(), reverse=True):
            if nights >= min_nights:
                applicable_discount = discount_multiplier
                break
        
        if applicable_discount:
            discount = base_total * (Decimal('1') - applicable_discount)
            base_total = base_total * applicable_discount
    
    # Calculate total
    total = base_total + cleaning_fee + service_fee
    
    return {
        'base_total': base_total,
        'nightly_prices': nightly_prices,
        'cleaning_fee': cleaning_fee,
        'service_fee': service_fee,
        'discount': discount,
        'total': total,
        'nights': nights
    }

def format_price(price: Decimal, currency: str = '₽') -> str:
    """
    Format a price with currency symbol
    """
    return f"{price:.0f} {currency}"

def calculate_host_payout(total: Decimal, host_fee_percentage: Decimal = Decimal('3')) -> Decimal:
    """
    Calculate the amount the host receives after platform fees
    """
    host_fee = total * (host_fee_percentage / Decimal('100'))
    return total - host_fee

def calculate_average_nightly_price(price_data: Dict[str, Union[Decimal, int]]) -> Decimal:
    """
    Calculate the average nightly price from a price calculation result
    """
    if price_data['nights'] == 0:
        return Decimal('0')
    
    return price_data['base_total'] / Decimal(price_data['nights'])

def apply_special_offer(total: Decimal, discount_percentage: Decimal) -> Tuple[Decimal, Decimal]:
    """
    Apply a special offer discount to the total price
    
    Returns:
        Tuple of (discounted_price, discount_amount)
    """
    discount_amount = total * (discount_percentage / Decimal('100'))
    discounted_price = total - discount_amount
    return (discounted_price, discount_amount)
