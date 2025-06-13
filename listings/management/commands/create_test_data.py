
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta, date

# Import models
from users.models import User
from subscriptions.models import SubscriptionPlan, UserSubscription, SubscriptionLog
from listings.models import Listing, Booking, Review, ListingImage
from moderation.models import (
    Report, ReportCategory, BannedUser, ListingApproval, 
    ModerationLog, UserComplaint, ForbiddenKeyword
)

class Command(BaseCommand):
    help = 'Create comprehensive test data for the platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating comprehensive test data...')
        
        if options['clear']:
            self.clear_test_data()
        
        with transaction.atomic():
            # Create data in correct order
            self.create_subscription_plans()
            self.create_users()
            self.create_report_categories()
            self.create_forbidden_keywords()
            self.create_listings()
            self.create_bookings()
            self.create_reviews()
            self.create_complaints()
            self.create_reports()
            
        self.stdout.write(
            self.style.SUCCESS('Successfully created all test data!')
        )

    def clear_test_data(self):
        """Clear existing test data"""
        self.stdout.write('Clearing existing test data...')
        
        # Clear in reverse dependency order
        UserComplaint.objects.filter(
            complainant__username__startswith='guest'
        ).delete()
        
        Report.objects.filter(
            reporter__username__startswith='guest'
        ).delete()
        
        Review.objects.filter(
            reviewer__username__startswith='guest'
        ).delete()
        
        Booking.objects.filter(
            guest__username__startswith='guest'
        ).delete()
        
        ListingApproval.objects.filter(
            listing__host__username__startswith='host'
        ).delete()
        
        Listing.objects.filter(
            host__username__startswith='host'
        ).delete()
        
        UserSubscription.objects.filter(
            user__username__in=[f'host{i}' for i in range(1, 7)]
        ).delete()
        
        User.objects.filter(
            username__in=['admin'] + 
            [f'moderator{i}' for i in range(1, 4)] +
            [f'host{i}' for i in range(1, 7)] +
            [f'guest{i}' for i in range(1, 21)]
        ).delete()
        
        # Clear plans if they exist
        SubscriptionPlan.objects.filter(
            name__in=['Free', 'Basic', 'Premium', 'Business', 'Enterprise']
        ).delete()

    def create_subscription_plans(self):
        """Create 5 subscription plans"""
        self.stdout.write('Creating subscription plans...')
        
        plans_data = [
            {
                'name': 'Free',
                'slug': 'free',
                'plan_type': 'basic',
                'description': 'Бесплатный план для начинающих',
                'price': Decimal('0.00'),
                'duration_days': 30,
                'ads_limit': 1,
                'featured_ads_limit': 0,
                'premium_features': []
            },
            {
                'name': 'Basic',
                'slug': 'basic',
                'plan_type': 'basic',
                'description': 'Базовый план для обычных пользователей',
                'price': Decimal('990.00'),
                'duration_days': 30,
                'ads_limit': 5,
                'featured_ads_limit': 1,
                'premium_features': ['priority_support']
            },
            {
                'name': 'Premium',
                'slug': 'premium',
                'plan_type': 'premium',
                'description': 'Премиум план для активных хостов',
                'price': Decimal('2990.00'),
                'duration_days': 30,
                'ads_limit': 15,
                'featured_ads_limit': 5,
                'premium_features': ['priority_support', 'analytics', 'custom_branding']
            },
            {
                'name': 'Business',
                'slug': 'business',
                'plan_type': 'business',
                'description': 'Бизнес план для профессиональных хостов',
                'price': Decimal('5990.00'),
                'duration_days': 30,
                'ads_limit': 50,
                'featured_ads_limit': 15,
                'premium_features': ['priority_support', 'analytics', 'custom_branding', 'api_access']
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'description': 'Корпоративный план для больших компаний',
                'price': Decimal('15990.00'),
                'duration_days': 30,
                'ads_limit': 200,
                'featured_ads_limit': 50,
                'premium_features': ['priority_support', 'analytics', 'custom_branding', 'api_access', 'dedicated_manager']
            }
        ]
        
        for plan_data in plans_data:
            SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )

    def create_users(self):
        """Create users: 1 admin, 3 moderators, 6 hosts, 20 guests"""
        self.stdout.write('Creating users...')
        
        # Create admin
        admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            first_name='Главный',
            last_name='Администратор',
            is_staff=True,
            is_superuser=True,
            role='admin',
            is_active=True
        )
        
        # Create moderators
        moderators = []
        for i in range(1, 4):
            moderator = User.objects.create_user(
                username=f'moderator{i}',
                email=f'moderator{i}@test.com',
                password='testpass123',
                first_name=f'Модератор{i}',
                last_name='Платформы',
                is_staff=True,
                role='moderator',
                is_active=True
            )
            moderators.append(moderator)
        
        # Create hosts with subscriptions
        hosts = []
        plans = list(SubscriptionPlan.objects.all())
        
        for i in range(1, 7):
            host = User.objects.create_user(
                username=f'host{i}',
                email=f'host{i}@test.com',
                password='testpass123',
                first_name=f'Хост{i}',
                last_name='Владелец',
                is_host=True,
                is_guest=True,
                role='host',
                is_active=True,
                phone_number=f'+7900123456{i}',
                is_phone_verified=True
            )
            hosts.append(host)
            
            # Create subscription for each host
            plan = random.choice(plans)
            start_date = timezone.now() - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(days=plan.duration_days)
            
            subscription = UserSubscription.objects.create(
                user=host,
                plan=plan,
                status='active' if end_date > timezone.now() else 'expired',
                start_date=start_date,
                end_date=end_date,
                amount_paid=plan.price,
                auto_renew=random.choice([True, False])
            )
            
            # Create subscription log
            SubscriptionLog.objects.create(
                subscription=subscription,
                action='created',
                description=f'Subscription created for plan {plan.name}',
                performed_by=admin
            )
        
        # Create guests
        guests = []
        for i in range(1, 21):
            guest = User.objects.create_user(
                username=f'guest{i}',
                email=f'guest{i}@test.com',
                password='testpass123',
                first_name=f'Гость{i}',
                last_name='Путешественник',
                is_guest=True,
                role='user',
                is_active=True,
                phone_number=f'+7900123450{i}' if i < 10 else f'+7900123450{i}',
                is_phone_verified=random.choice([True, False])
            )
            guests.append(guest)
        
        self.users = {
            'admin': admin,
            'moderators': moderators,
            'hosts': hosts,
            'guests': guests
        }

    def create_report_categories(self):
        """Create report categories"""
        categories = [
            {'name': 'Неподходящий контент', 'description': 'Контент не соответствует правилам'},
            {'name': 'Мошенничество', 'description': 'Подозрение в мошенничестве'},
            {'name': 'Спам', 'description': 'Спам или нежелательная реклама'},
            {'name': 'Оскорбления', 'description': 'Оскорбительные высказывания'},
            {'name': 'Дискриминация', 'description': 'Дискриминация по любому признаку'},
        ]
        
        for cat_data in categories:
            ReportCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )

    def create_forbidden_keywords(self):
        """Create forbidden keywords"""
        keywords = [
            {'keyword': 'мошенник', 'replacement': '***', 'severity': 3},
            {'keyword': 'дурак', 'replacement': '***', 'severity': 2},
            {'keyword': 'обман', 'replacement': 'недоразумение', 'severity': 2},
        ]
        
        for kw_data in keywords:
            ForbiddenKeyword.objects.get_or_create(
                keyword=kw_data['keyword'],
                defaults=kw_data
            )

    def create_listings(self):
        """Create ~10 listings per host with various statuses"""
        self.stdout.write('Creating listings...')
        
        property_types = ['Квартира', 'Дом', 'Коттедж', 'Студия', 'Лофт']
        cities = ['Москва', 'Санкт-Петербург', 'Казань', 'Сочи', 'Екатеринбург']
        amenities_list = [
            ['WiFi', 'Кухня', 'Стиральная машина'],
            ['WiFi', 'Парковка', 'Кондиционер'],
            ['WiFi', 'Телевизор', 'Холодильник'],
            ['WiFi', 'Балкон', 'Посудомоечная машина'],
        ]
        
        all_listings = []
        moderators = self.users['moderators']
        
        for host in self.users['hosts']:
            # Create 8-12 listings per host
            num_listings = random.randint(8, 12)
            
            for i in range(num_listings):
                city = random.choice(cities)
                property_type = random.choice(property_types)
                
                listing = Listing.objects.create(
                    title=f'{property_type} в {city} от {host.first_name}',
                    description=f'Уютный {property_type.lower()} в центре города {city}. Идеально подходит для отдыха.',
                    address=f'ул. Тестовая, {random.randint(1, 100)}',
                    city=city,
                    state='Московская область' if city == 'Москва' else 'Другая область',
                    country='Россия',
                    zip_code=f'{random.randint(100000, 999999)}',
                    price_per_night=Decimal(str(random.randint(2000, 15000))),
                    cleaning_fee=Decimal(str(random.randint(500, 2000))),
                    service_fee=Decimal(str(random.randint(300, 1000))),
                    bedrooms=random.randint(1, 4),
                    bathrooms=Decimal(str(random.choice([1, 1.5, 2, 2.5, 3]))),
                    accommodates=random.randint(2, 8),
                    property_type=property_type,
                    amenities=random.choice(amenities_list),
                    house_rules='Не курить, не шуметь после 22:00',
                    minimum_nights=random.randint(1, 3),
                    maximum_nights=random.randint(14, 90),
                    host=host,
                    is_active=random.choice([True, True, True, False]),  # 75% active
                    is_approved=False  # Will be set by approval process
                )
                
                # Create listing approval record
                moderator = random.choice(moderators)
                
                # Randomly determine approval status
                approval_status = random.choice([
                    'pending', 'approved', 'approved', 'approved',  # More approved
                    'rejected', 'requires_changes'
                ])
                
                approval = ListingApproval.objects.create(
                    listing=listing,
                    status=approval_status,
                    moderator=moderator if approval_status != 'pending' else None,
                    has_valid_title=True,
                    has_valid_description=True,
                    has_valid_images=random.choice([True, False]),
                    has_valid_address=True,
                    has_appropriate_pricing=True,
                    follows_content_policy=approval_status != 'rejected',
                    has_verification_video=random.choice([True, False])
                )
                
                # Set listing approval status
                if approval_status == 'approved':
                    listing.is_approved = True
                    listing.save()
                    
                    # Log approval
                    ModerationLog.objects.create(
                        moderator=moderator,
                        action_type='listing_approved',
                        target_listing=listing,
                        description=f'Listing "{listing.title}" approved',
                        notes='Meets all requirements'
                    )
                    
                elif approval_status == 'rejected':
                    approval.rejection_reason = 'Недостаточно информации об объекте'
                    approval.save()
                    
                    # Log rejection
                    ModerationLog.objects.create(
                        moderator=moderator,
                        action_type='listing_rejected',
                        target_listing=listing,
                        description=f'Listing "{listing.title}" rejected',
                        notes='Insufficient property information'
                    )
                
                # Only add active and approved listings to available listings
                if listing.is_active and listing.is_approved:
                    all_listings.append(listing)
        
        self.listings = all_listings
        self.all_listings_including_inactive = list(Listing.objects.all())

    def create_bookings(self):
        """Create 5-6 bookings per guest per month from 2023-2025"""
        self.stdout.write('Creating bookings...')
        
        if not self.listings:
            self.stdout.write(self.style.WARNING('No active approved listings found. Skipping bookings.'))
            return
        
        start_year = 2023
        end_year = 2025
        all_bookings = []
        
        for guest in self.users['guests']:
            guest_bookings = []
            
            # Generate bookings for each month from 2023 to 2025
            current_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            while current_date <= end_date:
                # Create 5-6 bookings per month
                bookings_this_month = random.randint(5, 6)
                
                for _ in range(bookings_this_month):
                    listing = random.choice(self.listings)
                    
                    # Random start date within the month
                    start_day = random.randint(1, 28)  # Safe day range
                    booking_start = date(current_date.year, current_date.month, start_day)
                    
                    # Random duration (1-7 nights)
                    nights = random.randint(1, 7)
                    booking_end = booking_start + timedelta(days=nights)
                    
                    # Skip if booking overlaps with existing bookings for this listing
                    if not self.check_availability(listing, booking_start, booking_end):
                        continue
                    
                    # Calculate pricing
                    price_calculation = listing.calculate_price(booking_start, booking_end)
                    
                    # Random status based on dates
                    now = timezone.now().date()
                    if booking_end < now:
                        status = random.choice(['completed', 'completed', 'completed', 'canceled'])
                    elif booking_start <= now <= booking_end:
                        status = 'confirmed'
                    else:
                        status = random.choice(['pending', 'confirmed'])
                    
                    booking = Booking.objects.create(
                        start_date=booking_start,
                        end_date=booking_end,
                        guests=random.randint(1, min(4, listing.accommodates)),
                        status=status,
                        base_price=price_calculation['base_price'],
                        cleaning_fee=price_calculation['cleaning_fee'],
                        service_fee=price_calculation['service_fee'],
                        total_price=price_calculation['total_price'],
                        special_requests=random.choice([
                            '', 'Ранний заезд', 'Поздний выезд', 
                            'Дополнительные полотенца', 'Тихий номер'
                        ]),
                        listing=listing,
                        guest=guest,
                        created_at=timezone.make_aware(
                            datetime.combine(booking_start - timedelta(days=random.randint(1, 30)), 
                                           datetime.min.time())
                        )
                    )
                    
                    guest_bookings.append(booking)
                    all_bookings.append(booking)
                
                # Move to next month
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, current_date.month + 1, 1)
        
        self.bookings = all_bookings

    def check_availability(self, listing, start_date, end_date):
        """Check if listing is available for given dates"""
        existing_bookings = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'completed'],
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        return not existing_bookings.exists()

    def create_reviews(self):
        """Create 3-10 reviews for each completed booking"""
        self.stdout.write('Creating reviews...')
        
        if not self.bookings:
            self.stdout.write(self.style.WARNING('No bookings found. Skipping reviews.'))
            return
        
        completed_bookings = [b for b in self.bookings if b.status == 'completed']
        
        for booking in completed_bookings:
            # Create 3-10 reviews for each listing the guest stayed at
            # But only one review per guest per listing
            existing_review = Review.objects.filter(
                listing=booking.listing,
                reviewer=booking.guest
            ).first()
            
            if not existing_review:
                review = Review.objects.create(
                    rating=random.randint(3, 5),  # Mostly positive reviews
                    comment=self.generate_review_comment(),
                    listing=booking.listing,
                    reviewer=booking.guest,
                    booking=booking,
                    is_approved=True,
                    created_at=booking.created_at + timedelta(
                        days=random.randint(1, 7)
                    )
                )

    def generate_review_comment(self):
        """Generate realistic review comments"""
        comments = [
            "Отличное место! Очень чисто и уютно. Хозяин отзывчивый.",
            "Хорошее расположение, рядом с центром. Рекомендую!",
            "Всё как на фотографиях. Комфортное проживание.",
            "Тихое место, хорошо для отдыха. Есть всё необходимое.",
            "Просторная квартира, удобная кровать. Приедем ещё!",
            "Неплохо в целом, но могло быть чище. Хозяин вежливый.",
            "Отличное соотношение цена-качество. Всё понравилось.",
            "Уютно и комфортно. WiFi работает отлично. Спасибо!",
        ]
        return random.choice(comments)

    def create_complaints(self):
        """Create 0-5 complaints per guest with different statuses"""
        self.stdout.write('Creating complaints...')
        
        if not self.bookings:
            self.stdout.write(self.style.WARNING('No bookings found. Skipping complaints.'))
            return
        
        moderators = self.users['moderators']
        complaint_types = [
            'booking_issue', 'listing_issue', 'host_behavior', 
            'cleanliness', 'safety_concern', 'false_listing'
        ]
        
        for guest in self.users['guests']:
            # 0-5 complaints per guest
            num_complaints = random.randint(0, 5)
            guest_bookings = [b for b in self.bookings if b.guest == guest]
            
            if not guest_bookings:
                continue
            
            for _ in range(num_complaints):
                booking = random.choice(guest_bookings)
                complaint_type = random.choice(complaint_types)
                
                status = random.choice([
                    'pending', 'in_progress', 'investigating', 
                    'resolved', 'dismissed'
                ])
                
                moderator = random.choice(moderators) if status != 'pending' else None
                
                complaint = UserComplaint.objects.create(
                    complainant=guest,
                    booking=booking,
                    listing=booking.listing,
                    reported_user=booking.listing.host,
                    complaint_type=complaint_type,
                    description=self.generate_complaint_description(complaint_type),
                    priority=random.choice(['low', 'medium', 'high']),
                    status=status,
                    assigned_moderator=moderator,
                    created_at=booking.created_at + timedelta(
                        days=random.randint(1, 30)
                    )
                )
                
                if status in ['resolved', 'dismissed'] and moderator:
                    complaint.moderator_response = "Жалоба рассмотрена и решена согласно политике платформы."
                    complaint.save()
                    
                    # Log moderation action
                    ModerationLog.objects.create(
                        moderator=moderator,
                        action_type='complaint_handled',
                        target_user=booking.listing.host,
                        description=f'Complaint #{complaint.id} {status}',
                        notes=f'Complaint type: {complaint_type}'
                    )

    def generate_complaint_description(self, complaint_type):
        """Generate realistic complaint descriptions"""
        descriptions = {
            'booking_issue': 'Проблемы с процессом бронирования, хост не отвечает',
            'listing_issue': 'Объявление не соответствует действительности',
            'host_behavior': 'Неадекватное поведение хоста во время заселения',
            'cleanliness': 'Квартира была грязной по приезду',
            'safety_concern': 'Проблемы с безопасностью в помещении',
            'false_listing': 'Ложная информация в описании объекта',
        }
        return descriptions.get(complaint_type, 'Общая жалоба на качество обслуживания')

    def create_reports(self):
        """Create various reports from guests"""
        self.stdout.write('Creating reports...')
        
        categories = list(ReportCategory.objects.all())
        if not categories:
            return
        
        moderators = self.users['moderators']
        
        # Create some listing reports
        for _ in range(20):
            guest = random.choice(self.users['guests'])
            listing = random.choice(self.all_listings_including_inactive)
            category = random.choice(categories)
            
            status = random.choice(['pending', 'in_progress', 'resolved', 'rejected'])
            moderator = random.choice(moderators) if status != 'pending' else None
            
            report = Report.objects.create(
                reporter=guest,
                content_type='listing',
                category=category,
                description=f'Жалоба на объявление: {category.description}',
                status=status,
                listing=listing,
                moderator=moderator,
                created_at=timezone.now() - timedelta(
                    days=random.randint(1, 90)
                )
            )
            
            if status in ['resolved', 'rejected'] and moderator:
                report.moderator_notes = f'Отчёт {status} модератором'
                report.action_taken = 'Приняты соответствующие меры' if status == 'resolved' else 'Жалоба отклонена'
                report.save()
                
                # Log moderation action
                ModerationLog.objects.create(
                    moderator=moderator,
                    action_type=f'report_{status}',
                    target_listing=listing,
                    report=report,
                    description=f'Report #{report.id} {status}',
                    notes=f'Category: {category.name}'
                )
