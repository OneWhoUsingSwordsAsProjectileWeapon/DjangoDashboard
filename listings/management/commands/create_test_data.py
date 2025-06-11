
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Review
from moderation.models import UserComplaint, ListingApproval
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
        for i in range(5):  # Увеличено количество хостов
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
        for i in range(8):  # Увеличено количество гостей
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
            hosts = list(User.objects.filter(is_host=True)[:5])
        
        if not guests:
            guests = list(User.objects.filter(is_guest=True)[:8])
        
        if not hosts:
            self.stdout.write(self.style.ERROR('No hosts available. Please create some hosts first.'))
            return
        
        # Create listings for hosts (удвоенное количество)
        listings = []
        property_types = ['Квартира', 'Дом', 'Студия', 'Лофт', 'Комната', 'Апартаменты', 'Пентхаус', 'Таунхаус']
        cities = ['Москва', 'Санкт-Петербург', 'Казань', 'Нижний Новгород', 'Екатеринбург', 'Новосибирск', 'Сочи', 'Калининград', 'Ростов-на-Дону', 'Уфа', 'Чита']
        
        descriptions = [
            'Уютная {} в центре города {}. Прекрасное место для отдыха.',
            'Современная {} в престижном районе {}. Идеально для командировок.',
            'Просторная {} с отличным видом в {}. Все удобства включены.',
            'Стильная {} в тихом районе {}. Рядом парк и транспорт.',
            'Комфортная {} для семейного отдыха в {}. Детская площадка во дворе.',
            'Элегантная {} в историческом центре {}. Множество достопримечательностей.',
            'Светлая {} с балконом в {}. Прекрасный вид на город.',
            'Дизайнерская {} в новостройке {}. Современный ремонт.',
        ]
        
        amenities_list = [
            ['Wi-Fi', 'Кухня', 'Стиральная машина'],
            ['Wi-Fi', 'Кухня', 'Кондиционер', 'Парковка'],
            ['Wi-Fi', 'Кухня', 'Джакузи', 'Балкон'],
            ['Wi-Fi', 'Кухня', 'Стиральная машина', 'Телевизор'],
            ['Wi-Fi', 'Кухня', 'Посудомоечная машина', 'Лифт'],
            ['Wi-Fi', 'Мини-кухня', 'Кондиционер'],
            ['Wi-Fi', 'Полная кухня', 'Стиральная машина', 'Сушилка', 'Парковка'],
        ]
        
        # Create more listings per host to reach ~40 total (удвоено)
        total_listings_needed = 40
        listings_per_host = total_listings_needed // len(hosts) if hosts else 0
        extra_listings = total_listings_needed % len(hosts) if hosts else 0
        
        for i, host in enumerate(hosts):
            num_listings = listings_per_host
            if i < extra_listings:
                num_listings += 1
                
            for j in range(num_listings):
                city = random.choice(cities)
                property_type = random.choice(property_types)
                description_template = random.choice(descriptions)
                
                # Generate more varied data
                bedrooms = random.randint(1, 4)
                bathrooms = random.choice([1, 1.5, 2, 2.5, 3])
                accommodates = random.randint(bedrooms, bedrooms * 2 + 2)
                
                # Разные статусы одобренности и активности
                approval_chance = random.random()
                if approval_chance < 0.6:  # 60% одобрено и активно
                    is_approved = True
                    is_active = True
                elif approval_chance < 0.8:  # 20% одобрено но неактивно
                    is_approved = True
                    is_active = False
                elif approval_chance < 0.9:  # 10% не одобрено
                    is_approved = False
                    is_active = False
                else:  # 10% ожидает одобрения
                    is_approved = False
                    is_active = True
                
                listing = Listing.objects.create(
                    title=f'{property_type} в {city} - {bedrooms} комн.',
                    description=description_template.format(property_type.lower(), city),
                    address=f'ул. {random.choice(["Центральная", "Ленина", "Пушкина", "Гагарина", "Мира", "Советская"])}, {random.randint(1, 200)}',
                    city=city,
                    state=f'{city} область',
                    country='Россия',
                    zip_code=f'{random.randint(100000, 999999)}',
                    price_per_night=Decimal(str(random.randint(1500, 12000))),
                    cleaning_fee=Decimal(str(random.randint(300, 2000))),
                    service_fee=Decimal(str(random.randint(200, 1000))),
                    bedrooms=bedrooms,
                    bathrooms=Decimal(str(bathrooms)),
                    accommodates=accommodates,
                    property_type=property_type,
                    amenities=random.choice(amenities_list),
                    minimum_nights=random.choice([1, 2, 3]),
                    maximum_nights=random.choice([7, 14, 30]),
                    host=host,
                    is_active=is_active,
                    is_approved=is_approved
                )
                listings.append(listing)
                
                # Создаем запись на одобрение для каждого объявления
                if not is_approved:
                    status = random.choice(['pending', 'requires_changes'])
                else:
                    status = 'approved'
                    
                ListingApproval.objects.create(
                    listing=listing,
                    status=status,
                    has_valid_title=random.choice([True, False]),
                    has_valid_description=random.choice([True, False]),
                    has_valid_images=random.choice([True, False]),
                    has_valid_address=random.choice([True, False]),
                    has_appropriate_pricing=random.choice([True, False]),
                    follows_content_policy=random.choice([True, False]),
                    has_verification_video=random.choice([True, False])
                )
                
                self.stdout.write(f'Created listing: {listing.title} (approved: {is_approved}, active: {is_active})')
        
        # Create bookings with non-conflicting dates (увеличенное количество)
        statuses = ['pending', 'confirmed', 'completed', 'canceled']
        status_weights = [0.15, 0.25, 0.5, 0.1]  # More completed bookings for better stats
        
        today = date.today()
        
        # Create more bookings for better statistics (100-160 bookings - удвоено)
        num_bookings = random.randint(100, 160)
        successful_bookings = 0
        
        for _ in range(num_bookings * 2):  # Try more times to ensure we get enough bookings
            if not guests or not listings or successful_bookings >= num_bookings:
                break
                
            available_listings = [l for l in listings if l.is_active and l.is_approved]
            if not available_listings:
                continue
                
            listing = random.choice(available_listings)
            guest = random.choice(guests)
            
            # Generate random dates with better distribution
            if random.random() > 0.7:  # 30% future bookings
                days_ahead = random.randint(1, 60)
                start_date = today + timedelta(days=days_ahead)
            else:  # 70% past bookings
                days_ago = random.randint(1, 365)  # Within last year
                start_date = today - timedelta(days=days_ago)
                
            duration = random.randint(1, 14)  # 1-14 nights
            end_date = start_date + timedelta(days=duration)
            
            # Check if dates are available
            if listing.is_available(start_date, end_date):
                # Calculate pricing
                price_data = listing.calculate_price(start_date, end_date)
                
                # Adjust status based on dates with more variety
                if start_date > today:
                    status = random.choices(['pending', 'confirmed'], weights=[0.4, 0.6])[0]
                elif end_date < today:
                    status = random.choices(['completed', 'canceled'], weights=[0.8, 0.2])[0]
                else:
                    status = 'confirmed'
                
                booking = Booking.objects.create(
                    listing=listing,
                    guest=guest,
                    start_date=start_date,
                    end_date=end_date,
                    guests=random.randint(1, min(listing.accommodates, 6)),
                    status=status,
                    base_price=price_data['base_price'],
                    cleaning_fee=price_data['cleaning_fee'],
                    service_fee=price_data['service_fee'],
                    total_price=price_data['total_price'],
                    special_requests=random.choice([
                        '', 'Поздний заезд', 'Раннее заселение', 
                        'Дополнительные полотенца', 'Детская кроватка',
                        'Тихий номер', 'Высокий этаж', 'Парковочное место'
                    ])
                )
                
                successful_bookings += 1
                
                # Create reviews for completed bookings
                if status == 'completed' and random.random() > 0.25:  # 75% chance of review
                    rating = random.choices([3, 4, 5], weights=[0.1, 0.3, 0.6])[0]  # Mostly good ratings
                    comments = {
                        3: ['Неплохо, но есть недочеты.', 'Средний уровень сервиса.', 'Ожидал большего.'],
                        4: ['Хорошее место, рекомендую!', 'Все понравилось, чисто и уютно.', 'Хорошее расположение, удобно добираться.'],
                        5: ['Отличное место, превзошло ожидания!', 'Идеально для отдыха!', 'Приятный хозяин, все как на фото.', 'Отдохнули прекрасно, спасибо!', 'Обязательно приедем еще!']
                    }
                    
                    Review.objects.create(
                        listing=listing,
                        reviewer=guest,
                        booking=booking,
                        rating=rating,
                        comment=random.choice(comments[rating])
                    )
                
                self.stdout.write(f'Created booking: {booking.booking_reference} ({status})')
        
        # Создаем жалобы
        all_bookings = list(Booking.objects.all())
        if all_bookings and guests:
            complaint_types = [
                'booking_issue', 'listing_issue', 'host_behavior', 'guest_behavior',
                'safety_concern', 'false_listing', 'cleanliness', 'other'
            ]
            
            complaint_descriptions = {
                'booking_issue': [
                    'Проблемы с заездом, хозяин не отвечает',
                    'Отменили бронирование в последний момент',
                    'Неправильные даты в подтверждении'
                ],
                'listing_issue': [
                    'Объявление не соответствует действительности',
                    'Квартира оказалась грязной',
                    'Нет заявленных удобств'
                ],
                'host_behavior': [
                    'Хозяин ведет себя неадекватно',
                    'Требует дополнительную плату',
                    'Нарушает границы приватности'
                ],
                'guest_behavior': [
                    'Гость нарушает правила дома',
                    'Оставил квартиру в ужасном состоянии',
                    'Шумное поведение'
                ],
                'safety_concern': [
                    'Проблемы с замками',
                    'Небезопасная территория',
                    'Неисправная электропроводка'
                ],
                'false_listing': [
                    'Фотографии не соответствуют реальности',
                    'Неверная информация о местоположении',
                    'Скрыты важные детали'
                ],
                'cleanliness': [
                    'Квартира была грязной при заезде',
                    'Постельное белье не свежее',
                    'Ванная комната в плохом состоянии'
                ],
                'other': [
                    'Проблемы с соседями',
                    'Шум от ремонта',
                    'Другие неудобства'
                ]
            }
            
            # Создаем 15-25 жалоб
            num_complaints = random.randint(15, 25)
            for _ in range(num_complaints):
                booking = random.choice(all_bookings)
                complaint_type = random.choice(complaint_types)
                
                # Определяем, кто подает жалобу
                if random.choice([True, False]):
                    complainant = booking.guest
                    reported_user = booking.listing.host
                else:
                    complainant = booking.listing.host
                    reported_user = booking.guest
                
                complaint = UserComplaint.objects.create(
                    complainant=complainant,
                    booking=booking,
                    listing=booking.listing,
                    reported_user=reported_user,
                    complaint_type=complaint_type,
                    description=random.choice(complaint_descriptions[complaint_type]),
                    priority=random.choice(['low', 'medium', 'high', 'urgent']),
                    status=random.choice(['pending', 'in_progress', 'investigating', 'resolved', 'dismissed'])
                )
                
                self.stdout.write(f'Created complaint: {complaint.id} ({complaint_type})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test data created successfully!\n'
                f'Hosts: {len(hosts)}\n'
                f'Guests: {len(guests)}\n'
                f'Listings: {len(listings)}\n'
                f'Bookings: {Booking.objects.count()}\n'
                f'Reviews: {Review.objects.count()}\n'
                f'Complaints: {UserComplaint.objects.count()}\n'
                f'Listing Approvals: {ListingApproval.objects.count()}'
            )
        )
