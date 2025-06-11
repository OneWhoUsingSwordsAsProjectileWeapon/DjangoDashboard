
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Review
from moderation.models import UserComplaint, ListingApproval, ReportCategory
from datetime import date, timedelta
import random
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data for the dashboard'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create report categories if they don't exist
        categories = [
            ('Неподходящий контент', 'Неподходящие фото или описание'),
            ('Мошенничество', 'Подозрение в мошенничестве'),
            ('Нарушение правил', 'Нарушение правил платформы'),
            ('Безопасность', 'Вопросы безопасности'),
            ('Качество сервиса', 'Низкое качество обслуживания'),
        ]
        
        report_categories = []
        for name, description in categories:
            category, created = ReportCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            report_categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create 5 test users (hosts and guests)
        hosts = []
        guests = []
        
        # Create hosts
        for i in range(6):
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
        for i in range(10):
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
        
        # Create more listings per host to reach ~40 total
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
                
                # Различные статусы модерации
                approval_status = random.choices(
                    [True, False], 
                    weights=[0.7, 0.3]  # 70% одобрены, 30% не одобрены
                )[0]
                
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
                    is_active=random.choice([True, True, True, False]),  # 75% active
                    is_approved=approval_status
                )
                listings.append(listing)
                
                # Создаем запись модерации для каждого листинга
                approval_statuses = ['pending', 'approved', 'rejected', 'requires_changes']
                if approval_status:
                    moderation_status = 'approved'
                else:
                    moderation_status = random.choice(['pending', 'rejected', 'requires_changes'])
                
                # Случайные значения для критериев модерации
                listing_approval = ListingApproval.objects.create(
                    listing=listing,
                    status=moderation_status,
                    has_valid_title=random.choice([True, True, False]),
                    has_valid_description=random.choice([True, True, False]),
                    has_valid_images=random.choice([True, False, False]),
                    has_valid_address=random.choice([True, True, False]),
                    has_appropriate_pricing=random.choice([True, True, False]),
                    follows_content_policy=random.choice([True, True, False]),
                    has_verification_video=random.choice([True, False, False, False]),
                    moderator_notes=random.choice([
                        '', 
                        'Требуется добавить больше фотографий',
                        'Цена кажется завышенной',
                        'Необходимо уточнить адрес',
                        'Описание слишком краткое',
                        'Все критерии соблюдены'
                    ]) if moderation_status != 'pending' else '',
                    rejection_reason=random.choice([
                        '',
                        'Неподходящие фотографии',
                        'Некорректная информация',
                        'Нарушение правил платформы'
                    ]) if moderation_status == 'rejected' else '',
                    required_changes=random.choice([
                        '',
                        'Добавить качественные фотографии',
                        'Исправить описание объекта',
                        'Обновить контактную информацию'
                    ]) if moderation_status == 'requires_changes' else ''
                )
                
                self.stdout.write(f'Created listing: {listing.title} (status: {moderation_status})')
        
        # Create bookings with non-conflicting dates
        statuses = ['pending', 'confirmed', 'completed', 'canceled']
        status_weights = [0.15, 0.25, 0.5, 0.1]  # More completed bookings for better stats
        
        today = date.today()
        
        # Create more bookings for better statistics (100-160 bookings)
        num_bookings = random.randint(100, 160)
        successful_bookings = 0
        
        for _ in range(num_bookings * 2):  # Try more times to ensure we get enough bookings
            if not guests or not listings or successful_bookings >= num_bookings:
                break
                
            listing = random.choice([l for l in listings if l.is_active and l.is_approved])
            if not listing:
                continue
                
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
                
                # Adjust status based on dates
                if start_date > today:
                    status = random.choices(['pending', 'confirmed'], weights=[0.3, 0.7])[0]
                elif end_date < today:
                    status = random.choices(['completed', 'canceled'], weights=[0.85, 0.15])[0]
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
        
        # Создаем жалобы пользователей
        all_users = list(hosts) + list(guests)
        all_bookings = list(Booking.objects.all())
        
        # Создаем 30-60 жалоб
        num_complaints = random.randint(30, 60)
        
        complaint_types = [
            'booking_issue', 'listing_issue', 'host_behavior', 'guest_behavior',
            'safety_concern', 'false_listing', 'discrimination', 'payment_issue',
            'cleanliness', 'other'
        ]
        
        complaint_descriptions = {
            'booking_issue': [
                'Проблемы с заездом в указанное время',
                'Хост не отвечает на сообщения',
                'Бронирование было отменено в последний момент',
                'Проблемы с ключами от квартиры'
            ],
            'listing_issue': [
                'Реальность не соответствует фотографиям',
                'Адрес указан неверно',
                'Удобства из списка отсутствуют',
                'Размер квартиры не соответствует описанию'
            ],
            'host_behavior': [
                'Хост был груб и неучтив',
                'Хост нарушил договоренности',
                'Хост требует дополнительную оплату',
                'Хост отказывается возвращать депозит'
            ],
            'guest_behavior': [
                'Гость нарушил правила дома',
                'Гость причинил ущерб имуществу',
                'Гость устроил шумную вечеринку',
                'Гость оставил мусор и грязь'
            ],
            'cleanliness': [
                'Квартира была грязной по приезду',
                'В ванной комнате плесень',
                'Постельное белье не свежее',
                'На кухне грязная посуда'
            ],
            'safety_concern': [
                'Подозрительные люди у входа',
                'Замки не работают должным образом',
                'Проблемы с электропроводкой',
                'Отсутствуют пожарные выходы'
            ]
        }
        
        for _ in range(num_complaints):
            if not all_users or not all_bookings:
                break
                
            complainant = random.choice(all_users)
            booking = random.choice(all_bookings)
            complaint_type = random.choice(complaint_types)
            
            # Определяем на кого жалуемся
            if complainant == booking.guest:
                reported_user = booking.listing.host
            elif complainant == booking.listing.host:
                reported_user = booking.guest
            else:
                # Случайная жалоба от третьего лица
                reported_user = random.choice([booking.guest, booking.listing.host])
            
            description_options = complaint_descriptions.get(complaint_type, ['Общая жалоба на сервис'])
            description = random.choice(description_options)
            
            status = random.choices(
                ['pending', 'in_progress', 'investigating', 'resolved', 'dismissed'],
                weights=[0.3, 0.2, 0.1, 0.3, 0.1]
            )[0]
            
            priority = random.choices(
                ['low', 'medium', 'high', 'urgent'],
                weights=[0.4, 0.4, 0.15, 0.05]
            )[0]
            
            # Получаем модератора (админа или модера)
            moderator = None
            if status != 'pending':
                try:
                    moderator = User.objects.filter(role__in=['admin', 'moderator']).first()
                except:
                    pass
            
            complaint = UserComplaint.objects.create(
                complainant=complainant,
                booking=booking,
                listing=booking.listing,
                reported_user=reported_user,
                complaint_type=complaint_type,
                description=description,
                priority=priority,
                status=status,
                assigned_moderator=moderator,
                moderator_response=random.choice([
                    '',
                    'Мы рассматриваем вашу жалобу',
                    'Проблема решена, спасибо за обращение',
                    'К сожалению, мы не можем подтвердить ваши претензии',
                    'Мы свяжемся с другой стороной для урегулирования'
                ]) if status != 'pending' else '',
                internal_notes=random.choice([
                    '',
                    'Требует дополнительной проверки',
                    'Повторная жалоба от этого пользователя',
                    'Необходимо связаться с хостом',
                    'Проблема урегулирована'
                ]) if moderator else ''
            )
            
            self.stdout.write(f'Created complaint: {complaint.id} ({complaint_type}, {status})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test data created successfully!\n'
                f'Hosts: {len(hosts)}\n'
                f'Guests: {len(guests)}\n'
                f'Listings: {len(listings)}\n'
                f'Bookings: {Booking.objects.count()}\n'
                f'Reviews: {Review.objects.count()}\n'
                f'Complaints: {UserComplaint.objects.count()}\n'
                f'Listing Approvals: {ListingApproval.objects.count()}\n'
                f'Report Categories: {len(report_categories)}'
            )
        )
