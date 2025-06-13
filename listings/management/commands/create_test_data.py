
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from listings.models import Listing, Booking, Review
from moderation.models import UserComplaint
from chat.models import Conversation, Message
from datetime import date, timedelta
import random
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create comprehensive test data with hosts, clients, listings, bookings, complaints, chats and reviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hosts',
            type=int,
            default=10,
            help='Number of hosts to create (default: 10)'
        )
        parser.add_argument(
            '--clients',
            type=int,
            default=20,
            help='Number of clients to create (default: 20)'
        )
        parser.add_argument(
            '--listings',
            type=int,
            default=50,
            help='Number of listings to create (default: 50)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=4000,
            help='Number of bookings to create (default: 4000)'
        )
        parser.add_argument(
            '--complaints',
            type=int,
            default=20,
            help='Number of complaints to create (default: 20)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating comprehensive test data...')
        
        num_hosts = options['hosts']
        num_clients = options['clients']
        num_listings = options['listings']
        num_bookings = options['bookings']
        num_complaints = options['complaints']
        
        # Create hosts
        hosts = []
        host_names = [
            'Александр', 'Елена', 'Дмитрий', 'Анна', 'Михаил', 'Ольга', 'Сергей', 'Мария',
            'Андрей', 'Татьяна', 'Владимир', 'Наталья', 'Николай', 'Екатерина', 'Алексей'
        ]
        host_surnames = [
            'Петров', 'Иванов', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Волков', 'Соколов',
            'Лебедев', 'Козлов', 'Новиков', 'Морозов', 'Петухов', 'Волошин', 'Белов'
        ]
        
        for i in range(num_hosts):
            first_name = random.choice(host_names)
            last_name = random.choice(host_surnames)
            username = f'host_{i+1}_{first_name.lower()}'
            email = f'{username}@example.com'
            
            if not User.objects.filter(email=email).exists():
                host = User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpass123',
                    first_name=first_name,
                    last_name=last_name,
                    is_host=True,
                    is_guest=False,
                    role='host',
                    phone_number=f'+7{random.randint(9000000000, 9999999999)}',
                    is_phone_verified=random.choice([True, False]),
                    is_id_verified=random.choice([True, False])
                )
                hosts.append(host)
                self.stdout.write(f'Created host: {host.username}')

        # Create clients (guests)
        clients = []
        client_names = [
            'Иван', 'Светлана', 'Павел', 'Юлия', 'Константин', 'Валентина', 'Роман', 'Людмила',
            'Артем', 'Галина', 'Максим', 'Вера', 'Игорь', 'Марина', 'Денис', 'Ирина', 'Федор',
            'Лариса', 'Кирилл', 'Зинаида', 'Георгий', 'Нина', 'Станислав', 'Любовь', 'Виктор'
        ]
        
        for i in range(num_clients):
            first_name = random.choice(client_names)
            last_name = random.choice(host_surnames)
            username = f'client_{i+1}_{first_name.lower()}'
            email = f'{username}@example.com'
            
            if not User.objects.filter(email=email).exists():
                client = User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpass123',
                    first_name=first_name,
                    last_name=last_name,
                    is_host=False,
                    is_guest=True,
                    role='user',
                    phone_number=f'+7{random.randint(9000000000, 9999999999)}',
                    is_phone_verified=random.choice([True, False]),
                    is_id_verified=random.choice([True, False])
                )
                clients.append(client)
                self.stdout.write(f'Created client: {client.username}')

        # Create listings
        listings = []
        property_types = ['Квартира', 'Дом', 'Студия', 'Лофт', 'Комната', 'Апартаменты', 'Пентхаус', 'Таунхаус', 'Коттедж', 'Гостевой дом']
        cities = [
            'Москва', 'Санкт-Петербург', 'Казань', 'Нижний Новгород', 'Екатеринбург', 
            'Новосибирск', 'Сочи', 'Калининград', 'Ростов-на-Дону', 'Уфа', 'Чита',
            'Краснодар', 'Владивосток', 'Иркутск', 'Томск', 'Тюмень', 'Архангельск'
        ]
        
        descriptions = [
            'Уютная {} в центре города {}. Прекрасное место для отдыха с семьей.',
            'Современная {} в престижном районе {}. Идеально для командировок и деловых поездок.',
            'Просторная {} с отличным видом в {}. Все удобства включены, парковка бесплатная.',
            'Стильная {} в тихом районе {}. Рядом парк и удобный транспорт.',
            'Комфортная {} для семейного отдыха в {}. Детская площадка во дворе.',
            'Элегантная {} в историческом центре {}. Множество достопримечательностей рядом.',
            'Светлая {} с балконом в {}. Прекрасный вид на город и реку.',
            'Дизайнерская {} в новостройке {}. Современный ремонт и техника.',
            'Домашняя {} в спокойном месте {}. Отличное место для восстановления сил.',
            'Роскошная {} с террасой в {}. VIP уровень комфорта и сервиса.'
        ]
        
        amenities_list = [
            ['Wi-Fi', 'Кухня', 'Стиральная машина', 'Телевизор'],
            ['Wi-Fi', 'Кухня', 'Кондиционер', 'Парковка', 'Балкон'],
            ['Wi-Fi', 'Кухня', 'Джакузи', 'Балкон', 'Сауна'],
            ['Wi-Fi', 'Кухня', 'Стиральная машина', 'Телевизор', 'Микроволновка'],
            ['Wi-Fi', 'Кухня', 'Посудомоечная машина', 'Лифт', 'Консьерж'],
            ['Wi-Fi', 'Мини-кухня', 'Кондиционер', 'Сейф'],
            ['Wi-Fi', 'Полная кухня', 'Стиральная машина', 'Сушилка', 'Парковка', 'Терраса'],
            ['Wi-Fi', 'Кухня', 'Камин', 'Барбекю', 'Сад'],
            ['Wi-Fi', 'Кухня', 'Бассейн', 'Спортзал', 'Охрана'],
            ['Wi-Fi', 'Кухня', 'Кондиционер', 'Отопление', 'Интернет']
        ]
        
        for i in range(num_listings):
            if not hosts:
                break
                
            host = random.choice(hosts)
            city = random.choice(cities)
            property_type = random.choice(property_types)
            description_template = random.choice(descriptions)
            
            bedrooms = random.randint(1, 5)
            bathrooms = random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4])
            accommodates = random.randint(bedrooms, bedrooms * 3 + 2)
            
            listing = Listing.objects.create(
                title=f'{property_type} "{random.choice(["Уют", "Комфорт", "Люкс", "Стандарт", "Премиум", "Эконом", "Бизнес", "Семейный", "VIP", "Классик"])}" в {city}',
                description=description_template.format(property_type.lower(), city),
                address=f'ул. {random.choice(["Центральная", "Ленина", "Пушкина", "Гагарина", "Мира", "Советская", "Новая", "Садовая", "Парковая", "Речная"])}, {random.randint(1, 300)}',
                city=city,
                state=f'{city} область',
                country='Россия',
                zip_code=f'{random.randint(100000, 999999)}',
                latitude=Decimal(str(random.uniform(55.0, 60.0))),
                longitude=Decimal(str(random.uniform(30.0, 40.0))),
                price_per_night=Decimal(str(random.randint(1000, 25000))),
                cleaning_fee=Decimal(str(random.randint(200, 3000))),
                service_fee=Decimal(str(random.randint(100, 1500))),
                bedrooms=bedrooms,
                bathrooms=Decimal(str(bathrooms)),
                accommodates=accommodates,
                property_type=property_type,
                amenities=random.choice(amenities_list),
                house_rules=random.choice([
                    'Не курить в помещении. Тихие часы после 22:00.',
                    'Запрещены вечеринки. Уборка обязательна.',
                    'Домашние животные не допускаются.',
                    'Максимум 2 гостя сверх заявленного.',
                    'Заезд строго по времени. Выезд до 12:00.'
                ]),
                minimum_nights=random.choice([1, 2, 3, 7]),
                maximum_nights=random.choice([7, 14, 30, 90]),
                host=host,
                is_active=random.choice([True, True, True, False]),
                is_approved=random.choice([True, True, True, False])
            )
            listings.append(listing)
            self.stdout.write(f'Created listing: {listing.title}')

        # Create bookings with realistic distribution over the year
        bookings = []
        statuses = ['pending', 'confirmed', 'completed', 'canceled']
        status_weights = [0.1, 0.2, 0.6, 0.1]  # 60% completed for good statistics
        
        today = date.today()
        start_of_year = today - timedelta(days=365)
        
        successful_bookings = 0
        max_attempts = num_bookings * 5  # Try more times to ensure we get enough bookings
        
        for attempt in range(max_attempts):
            if successful_bookings >= num_bookings or not clients or not listings:
                break
                
            # Select available listing
            available_listings = [l for l in listings if l.is_active and l.is_approved]
            if not available_listings:
                continue
                
            listing = random.choice(available_listings)
            client = random.choice(clients)
            
            # Generate dates more evenly distributed throughout the year
            days_from_start = random.randint(0, 365)
            start_date = start_of_year + timedelta(days=days_from_start)
            duration = random.randint(1, 21)  # 1-21 nights
            end_date = start_date + timedelta(days=duration)
            
            # Check availability
            if listing.is_available(start_date, end_date):
                # Calculate pricing
                price_data = listing.calculate_price(start_date, end_date)
                
                # Determine status based on dates
                if start_date > today:
                    status = random.choices(['pending', 'confirmed'], weights=[0.3, 0.7])[0]
                elif end_date < today:
                    status = random.choices(['completed', 'canceled'], weights=[0.85, 0.15])[0]
                else:
                    status = 'confirmed'
                
                booking = Booking.objects.create(
                    listing=listing,
                    guest=client,
                    start_date=start_date,
                    end_date=end_date,
                    guests=random.randint(1, min(listing.accommodates, 8)),
                    status=status,
                    base_price=price_data['base_price'],
                    cleaning_fee=price_data['cleaning_fee'],
                    service_fee=price_data['service_fee'],
                    total_price=price_data['total_price'],
                    special_requests=random.choice([
                        '', 'Поздний заезд после 20:00', 'Раннее заселение до 12:00', 
                        'Дополнительные полотенца', 'Детская кроватка',
                        'Тихий номер', 'Высокий этаж', 'Парковочное место',
                        'Встреча в аэропорту', 'Дополнительные подушки',
                        'Гипоаллергенное белье', 'Трансфер от метро'
                    ])
                )
                
                bookings.append(booking)
                successful_bookings += 1
                
                if successful_bookings % 500 == 0:
                    self.stdout.write(f'Created {successful_bookings} bookings...')

        self.stdout.write(f'Created {len(bookings)} bookings total')

        # Create reviews for completed bookings (5-7 per listing max)
        reviews_created = 0
        listing_review_counts = {}
        
        for booking in bookings:
            if booking.status == 'completed':
                listing_id = booking.listing.id
                current_count = listing_review_counts.get(listing_id, 0)
                
                # Only create review if listing has less than 7 reviews and random chance
                if current_count < 7 and random.random() > 0.3:  # 70% chance of review
                    rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.05, 0.15, 0.35, 0.4])[0]
                
                comments = {
                    1: ['Очень плохо, не рекомендую.', 'Ужасные условия.', 'Полное разочарование.'],
                    2: ['Не очень, есть проблемы.', 'Много недостатков.', 'Ожидал лучшего.'],
                    3: ['Средне, есть недочеты.', 'Неплохо, но можно лучше.', 'Удовлетворительно.'],
                    4: ['Хорошо, рекомендую!', 'Приятное место.', 'Хороший уровень сервиса.'],
                    5: ['Отлично! Превзошло ожидания!', 'Идеальное место!', 'Всё было perfect!']
                }
                
                Review.objects.create(
                        listing=booking.listing,
                        reviewer=booking.guest,
                        booking=booking,
                        rating=rating,
                        comment=random.choice(comments[rating]),
                        is_approved=random.choice([True, True, True, False])  # 75% approved
                    )
                    reviews_created += 1
                    listing_review_counts[listing_id] = current_count + 1

        self.stdout.write(f'Created {reviews_created} reviews')

        # Create conversations and messages for bookings
        conversations_created = 0
        messages_created = 0
        
        for booking in random.sample(bookings, min(len(bookings), num_bookings // 2)):  # 50% of bookings have chats
            # Create conversation between guest and host
            conversation, created = Conversation.objects.get_or_create(
                booking=booking,
                defaults={
                    'participant1': booking.guest,
                    'participant2': booking.listing.host
                }
            )
            
            if created:
                conversations_created += 1
                
                # Create messages
                num_messages = random.randint(2, 15)
                current_time = booking.created_at
                
                messages = [
                    # Guest messages
                    f"Здравствуйте! Интересует ваше жилье на {booking.start_date.strftime('%d.%m.%Y')}",
                    "Можно ли заехать немного позже указанного времени?",
                    "Есть ли рядом продуктовые магазины?",
                    "Спасибо за быстрый ответ!",
                    "Как добраться от аэропорта?",
                    "Можно ли оставить багаж до заселения?",
                    "Отличное место, спасибо!",
                    
                    # Host messages  
                    "Здравствуйте! Конечно, жилье свободно в эти даты.",
                    "Да, заезд возможен до 21:00.",
                    "Рядом есть супермаркет, 5 минут пешком.",
                    "Пожалуйста! Всегда готов помочь.",
                    "Лучше всего на такси, примерно 30 минут.",
                    "Да, можете оставить в камере хранения у консьержа.",
                    "Спасибо за отзыв! Рады были вас видеть!",
                ]
                
                for i in range(num_messages):
                    is_from_guest = i % 2 == 0
                    sender = booking.guest if is_from_guest else booking.listing.host
                    
                    Message.objects.create(
                        conversation=conversation,
                        sender=sender,
                        content=random.choice(messages),
                        timestamp=current_time + timedelta(minutes=random.randint(30, 1440))
                    )
                    messages_created += 1
                    current_time += timedelta(minutes=random.randint(30, 1440))

        self.stdout.write(f'Created {conversations_created} conversations with {messages_created} messages')

        # Create complaints with different statuses
        complaints_created = 0
        complaint_types = [
            'booking_issue', 'listing_issue', 'host_behavior', 'guest_behavior',
            'safety_concern', 'false_listing', 'discrimination', 'payment_issue',
            'cleanliness', 'other'
        ]
        
        complaint_statuses = ['pending', 'in_progress', 'investigating', 'awaiting_response', 'resolved', 'dismissed', 'escalated']
        status_weights = [0.2, 0.15, 0.1, 0.1, 0.3, 0.1, 0.05]
        
        priorities = ['low', 'medium', 'high', 'urgent']
        priority_weights = [0.3, 0.5, 0.15, 0.05]
        
        complaint_descriptions = {
            'booking_issue': [
                'Проблемы с подтверждением бронирования',
                'Хост отменил бронирование в последний момент',
                'Даты бронирования не соответствуют заявленным'
            ],
            'listing_issue': [
                'Объявление не соответствует действительности',
                'Фотографии не отражают реальное состояние',
                'Указаны неверные удобства'
            ],
            'host_behavior': [
                'Хост ведет себя неподобающе',
                'Грубое обращение со стороны хоста',
                'Хост требует дополнительную плату'
            ],
            'guest_behavior': [
                'Гость нарушает правила дома',
                'Неуважительное поведение гостя',
                'Гость причинил ущерб имуществу'
            ],
            'safety_concern': [
                'Проблемы с безопасностью в жилье',
                'Неработающие замки или сигнализация',
                'Подозрительная активность в районе'
            ],
            'cleanliness': [
                'Жилье было грязным при заселении',
                'Проблемы с уборкой',
                'Неприятные запахи в помещении'
            ]
        }
        
        # Get moderators for assignment
        moderators = list(User.objects.filter(role__in=['moderator', 'admin']))
        
        for i in range(num_complaints):
            if not bookings:
                break
                
            booking = random.choice(bookings)
            complaint_type = random.choice(complaint_types)
            status = random.choices(complaint_statuses, weights=status_weights)[0]
            priority = random.choices(priorities, weights=priority_weights)[0]
            
            # Determine complainant (guest or host)
            complainant = random.choice([booking.guest, booking.listing.host])
            
            UserComplaint.objects.create(
                complainant=complainant,
                booking=booking,
                listing=booking.listing,
                complaint_type=complaint_type,
                description=random.choice(complaint_descriptions.get(complaint_type, ['Общая жалоба'])),
                priority=priority,
                status=status,
                assigned_moderator=random.choice(moderators) if moderators and random.random() > 0.3 else None,
                moderator_response=random.choice([
                    'Жалоба принята в работу',
                    'Требуется дополнительная информация',
                    'Проблема решена',
                    'Жалоба необоснована'
                ]) if status in ['resolved', 'dismissed'] else '',
                contact_email=complainant.email,
                created_at=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            complaints_created += 1

        self.stdout.write(f'Created {complaints_created} complaints')

        # Create subscription plans
        from subscriptions.models import SubscriptionPlan, UserSubscription, SubscriptionUsage
        from decimal import Decimal
        
        plans_created = 0
        subscriptions_created = 0
        
        # Create subscription plans if they don't exist
        plans_data = [
            {
                'name': 'Базовый',
                'slug': 'basic',
                'plan_type': 'basic',
                'description': 'Базовый план для новых пользователей',
                'price': Decimal('999.00'),
                'duration_days': 30,
                'ads_limit': 3,
                'featured_ads_limit': 0,
                'premium_features': ['basic_support'],
                'is_popular': False
            },
            {
                'name': 'Премиум',
                'slug': 'premium',
                'plan_type': 'premium',
                'description': 'Премиум план с расширенными возможностями',
                'price': Decimal('1999.00'),
                'duration_days': 30,
                'ads_limit': 10,
                'featured_ads_limit': 2,
                'premium_features': ['priority_support', 'analytics', 'featured_listings'],
                'is_popular': True
            },
            {
                'name': 'Бизнес',
                'slug': 'business',
                'plan_type': 'business',
                'description': 'Бизнес план для профессиональных хостов',
                'price': Decimal('4999.00'),
                'duration_days': 30,
                'ads_limit': 50,
                'featured_ads_limit': 10,
                'premium_features': ['priority_support', 'analytics', 'featured_listings', 'api_access'],
                'is_popular': False
            },
            {
                'name': 'Корпоративный',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'description': 'Корпоративный план без ограничений',
                'price': Decimal('9999.00'),
                'duration_days': 30,
                'ads_limit': 999,
                'featured_ads_limit': 50,
                'premium_features': ['priority_support', 'analytics', 'featured_listings', 'api_access', 'white_label'],
                'is_popular': False
            }
        ]
        
        created_plans = []
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            if created:
                plans_created += 1
            created_plans.append(plan)
        
        # Create subscription history for 2 years
        from dateutil.relativedelta import relativedelta
        
        all_users = hosts + clients
        today = timezone.now().date()
        start_date = today - timedelta(days=730)  # 2 years ago
        
        # Create subscriptions for users over 2 years
        for user in random.sample(all_users, min(len(all_users), 80)):  # 80% of users have subscriptions
            # Each user can have multiple subscriptions over 2 years
            num_subscriptions = random.randint(1, 6)  # 1-6 subscriptions per user
            
            for i in range(num_subscriptions):
                plan = random.choice(created_plans)
                
                # Random start date within 2 years
                days_from_start = random.randint(0, 700)  # Leave some space for subscription duration
                sub_start = start_date + timedelta(days=days_from_start)
                sub_end = sub_start + timedelta(days=plan.duration_days)
                
                # Determine status based on end date
                if sub_end < today:
                    if random.random() < 0.8:  # 80% completed naturally
                        status = 'expired'
                    else:
                        status = 'canceled'
                elif sub_start <= today <= sub_end:
                    status = 'active'
                else:
                    status = 'pending'
                
                # Create subscription
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    status=status,
                    start_date=timezone.make_aware(datetime.combine(sub_start, timezone.now().time())),
                    end_date=timezone.make_aware(datetime.combine(sub_end, timezone.now().time())),
                    auto_renew=random.choice([True, False]),
                    amount_paid=plan.price * Decimal(random.uniform(0.8, 1.2)),  # Some variation in pricing
                    created_at=timezone.make_aware(datetime.combine(sub_start, timezone.now().time())),
                )
                
                # Create usage tracking
                ads_count = random.randint(0, min(plan.ads_limit, len([l for l in listings if l.host == user])))
                SubscriptionUsage.objects.create(
                    subscription=subscription,
                    ads_count=ads_count,
                    featured_ads_count=random.randint(0, min(plan.featured_ads_limit, ads_count)),
                    total_ads_created=random.randint(ads_count, ads_count + 5),
                    last_ad_created=timezone.now() - timedelta(days=random.randint(1, 30)) if ads_count > 0 else None
                )
                
                subscriptions_created += 1
        
        self.stdout.write(f'Created {plans_created} subscription plans')
        self.stdout.write(f'Created {subscriptions_created} user subscriptions')

        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Comprehensive test data created successfully! ===\n'
                f'Hosts: {len(hosts)}\n'
                f'Clients: {len(clients)}\n'
                f'Listings: {len(listings)}\n'
                f'Bookings: {len(bookings)}\n'
                f'Reviews: {reviews_created}\n'
                f'Conversations: {conversations_created}\n'
                f'Messages: {messages_created}\n'
                f'Complaints: {complaints_created}\n'
                f'Subscription Plans: {plans_created}\n'
                f'User Subscriptions: {subscriptions_created}\n'
                f'\nTotal users in system: {User.objects.count()}\n'
                f'Active listings: {Listing.objects.filter(is_active=True).count()}\n'
                f'Completed bookings: {Booking.objects.filter(status="completed").count()}\n'
                f'Active subscriptions: {UserSubscription.objects.filter(status="active").count() if "UserSubscription" in locals() else 0}'
            )
        )
