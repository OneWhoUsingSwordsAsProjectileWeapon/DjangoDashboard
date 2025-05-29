
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Review
from datetime import date, timedelta
import random
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data for the dashboard'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create 5 test users (hosts and guests)
        hosts = []
        guests = []
        
        # Create hosts
        for i in range(3):
            email = f'host{i+1}@example.com'
            if not User.objects.filter(email=email).exists():
                host = User.objects.create_user(
                    username=f'host{i+1}',
                    email=email,
                    password='testpass123',
                    first_name=f'Host{i+1}',
                    last_name='User',
                    is_host=True,
                    is_guest=False
                )
                hosts.append(host)
                self.stdout.write(f'Created host: {host.username}')
        
        # Create guests
        for i in range(5):
            email = f'guest{i+1}@example.com'
            if not User.objects.filter(email=email).exists():
                guest = User.objects.create_user(
                    username=f'guest{i+1}',
                    email=email,
                    password='testpass123',
                    first_name=f'Guest{i+1}',
                    last_name='User',
                    is_host=False,
                    is_guest=True
                )
                guests.append(guest)
                self.stdout.write(f'Created guest: {guest.username}')
        
        # Get existing hosts if any
        if not hosts:
            hosts = list(User.objects.filter(is_host=True)[:3])
        
        if not guests:
            guests = list(User.objects.filter(is_guest=True)[:5])
        
        if not hosts:
            self.stdout.write(self.style.ERROR('No hosts available. Please create some hosts first.'))
            return
        
        # Create listings for hosts
        listings = []
        property_types = ['Квартира', 'Дом', 'Студия', 'Лофт', 'Комната']
        cities = ['Москва', 'Санкт-Петербург', 'Казань', 'Нижний Новгород', 'Екатеринбург']
        
        for host in hosts:
            for i in range(random.randint(2, 4)):
                city = random.choice(cities)
                property_type = random.choice(property_types)
                
                listing = Listing.objects.create(
                    title=f'{property_type} в центре {city}',
                    description=f'Уютная {property_type.lower()} в центре города {city}. Прекрасное место для отдыха.',
                    address=f'ул. Центральная, {random.randint(1, 100)}',
                    city=city,
                    state=f'{city} область',
                    country='Россия',
                    zip_code=f'{random.randint(100000, 999999)}',
                    price_per_night=Decimal(str(random.randint(2000, 8000))),
                    cleaning_fee=Decimal(str(random.randint(500, 1500))),
                    service_fee=Decimal(str(random.randint(300, 800))),
                    bedrooms=random.randint(1, 3),
                    bathrooms=Decimal(str(random.choice([1, 1.5, 2, 2.5]))),
                    accommodates=random.randint(2, 6),
                    property_type=property_type,
                    host=host,
                    is_active=True,
                    is_approved=True
                )
                listings.append(listing)
                self.stdout.write(f'Created listing: {listing.title}')
        
        # Create bookings with non-conflicting dates
        statuses = ['pending', 'confirmed', 'completed', 'canceled']
        status_weights = [0.1, 0.3, 0.5, 0.1]  # More completed bookings for better stats
        
        today = date.today()
        
        for _ in range(25):  # Create 25 bookings
            if not guests or not listings:
                break
                
            listing = random.choice(listings)
            guest = random.choice(guests)
            
            # Generate random dates
            days_ago = random.randint(1, 180)  # Within last 6 months
            start_date = today - timedelta(days=days_ago)
            duration = random.randint(2, 7)  # 2-7 nights
            end_date = start_date + timedelta(days=duration)
            
            # Check if dates are available
            if listing.is_available(start_date, end_date):
                # Calculate pricing
                price_data = listing.calculate_price(start_date, end_date)
                
                status = random.choices(statuses, weights=status_weights)[0]
                
                booking = Booking.objects.create(
                    listing=listing,
                    guest=guest,
                    start_date=start_date,
                    end_date=end_date,
                    guests=random.randint(1, listing.accommodates),
                    status=status,
                    base_price=price_data['base_price'],
                    cleaning_fee=price_data['cleaning_fee'],
                    service_fee=price_data['service_fee'],
                    total_price=price_data['total_price'],
                    special_requests=random.choice([
                        '', 'Поздний заезд', 'Раннее заселение', 
                        'Дополнительные полотенца', 'Детская кроватка'
                    ])
                )
                
                # Create reviews for completed bookings
                if status == 'completed' and random.random() > 0.3:  # 70% chance of review
                    Review.objects.create(
                        listing=listing,
                        reviewer=guest,
                        booking=booking,
                        rating=random.randint(3, 5),  # Mostly good ratings
                        comment=random.choice([
                            'Отличное место, рекомендую!',
                            'Все понравилось, чисто и уютно.',
                            'Хорошее расположение, удобно добираться.',
                            'Приятный хозяин, все как на фото.',
                            'Отдохнули прекрасно, спасибо!'
                        ])
                    )
                
                self.stdout.write(f'Created booking: {booking.booking_reference} ({status})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test data created successfully!\n'
                f'Hosts: {len(hosts)}\n'
                f'Guests: {len(guests)}\n'
                f'Listings: {len(listings)}\n'
                f'Bookings: {Booking.objects.count()}\n'
                f'Reviews: {Review.objects.count()}'
            )
        )
