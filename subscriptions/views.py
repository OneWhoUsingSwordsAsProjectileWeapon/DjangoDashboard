
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404, render
from django.db import transaction
from .models import SubscriptionPlan, UserSubscription, SubscriptionUsage
from .serializers import (
    SubscriptionPlanSerializer, UserSubscriptionSerializer,
    SubscriptionUsageSerializer, SubscriptionStatusSerializer,
    CreateSubscriptionSerializer, AdCreationCheckSerializer,
    SubscriptionStatsSerializer
)
from .services import SubscriptionService
import logging

logger = logging.getLogger(__name__)

def subscription_plans_view(request):
    """Web view for subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    return render(request, 'subscriptions/plan_list.html', {'plans': plans})

def admin_dashboard(request):
    """Admin dashboard for subscription management"""
    if not request.user.is_staff:
        from django.contrib.auth.decorators import user_passes_test
        return user_passes_test(lambda u: u.is_staff)(lambda r: None)(request)
    return render(request, 'subscriptions/admin_dashboard.html')

class SubscriptionPlanListView(generics.ListAPIView):
    """List all available subscription plans"""
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]

class UserSubscriptionListView(generics.ListAPIView):
    """List user's subscriptions"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user).order_by('-created_at')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def subscription_status(request):
    """Get current subscription status for user"""
    user = request.user
    
    # Get subscription limits
    limits = SubscriptionService.get_ads_limits(user.id)
    
    # Prepare response data
    data = {
        'has_subscription': limits['subscription_status'] not in ['none', 'error'],
        'plan_name': limits['plan_name'],
        'subscription_status': limits['subscription_status'],
        'current_ads': limits['current'],
        'ads_limit': limits['limit'],
        'expires_at': limits.get('expires_at'),
        'days_remaining': limits.get('days_remaining'),
        'usage_percentage': (limits['current'] / limits['limit'] * 100) if limits['limit'] > 0 else None
    }
    
    serializer = SubscriptionStatusSerializer(data)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def process_qr_payment(request):
    """Process QR code payment (test mode - auto approve)"""
    import json
    
    try:
        # Extract payment data from QR scan
        qr_data = request.data.get('qr_data')
        if not qr_data:
            return Response({
                'success': False,
                'message': _('No QR data provided')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse QR data
        if isinstance(qr_data, str):
            try:
                payment_data = json.loads(qr_data)
            except json.JSONDecodeError:
                return Response({
                    'success': False,
                    'message': _('Invalid QR data format')
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            payment_data = qr_data
        
        # Validate payment data
        required_fields = ['action', 'plan_id', 'test_mode']
        for field in required_fields:
            if field not in payment_data:
                return Response({
                    'success': False,
                    'message': _('Missing required field: {}').format(field)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if payment_data.get('action') != 'subscription_payment':
            return Response({
                'success': False,
                'message': _('Invalid payment action')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # In test mode, auto-approve payment
        if payment_data.get('test_mode'):
            # Get user ID from request (authenticated user)
            user_id = request.data.get('user_id')
            if not user_id and request.user.is_authenticated:
                user_id = request.user.id
                
            if not user_id:
                return Response({
                    'success': False,
                    'message': _('User authentication required')
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _('User not found')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get plan
            try:
                plan = SubscriptionPlan.objects.get(id=payment_data['plan_id'])
            except SubscriptionPlan.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _('Subscription plan not found')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create subscription
            with transaction.atomic():
                payment_ref = payment_data.get('payment_reference')
                if not payment_ref:
                    # Generate UUID if not provided
                    import uuid
                    payment_ref = str(uuid.uuid4())
                
                subscription = SubscriptionService.create_subscription(
                    user=user,
                    plan=plan,
                    payment_reference=payment_ref,
                    auto_renew=payment_data.get('auto_renew', False)
                )
                
                logger.info(f"QR payment processed for user {user.username}, subscription {subscription.id}")
                
                return Response({
                    'success': True,
                    'message': _('Payment processed successfully'),
                    'subscription_id': subscription.id,
                    'plan_name': plan.name
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': _('Only test payments are supported')
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error processing QR payment: {e}")
        return Response({
            'success': False,
            'message': _('Error processing payment'),
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_subscription(request):
    """Create a new subscription for user"""
    serializer = CreateSubscriptionSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                plan = get_object_or_404(SubscriptionPlan, id=serializer.validated_data['plan_id'])
                
                subscription = SubscriptionService.create_subscription(
                    user=request.user,
                    plan=plan,
                    payment_reference=serializer.validated_data.get('payment_reference'),
                    auto_renew=serializer.validated_data.get('auto_renew', False)
                )
                
                response_serializer = UserSubscriptionSerializer(subscription)
                
                logger.info(f"Created subscription {subscription.id} for user {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': _('Subscription created successfully'),
                    'subscription': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating subscription for user {request.user.username}: {e}")
            return Response({
                'success': False,
                'message': _('Error creating subscription'),
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'message': _('Invalid data'),
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_auto_renew(request):
    """Toggle auto-renewal for user's current subscription"""
    current_subscription = SubscriptionService.get_current_subscription(request.user)
    
    if not current_subscription:
        return Response({
            'success': False,
            'message': _('No active subscription found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    current_subscription.auto_renew = not current_subscription.auto_renew
    current_subscription.save(update_fields=['auto_renew'])
    
    return Response({
        'success': True,
        'auto_renew': current_subscription.auto_renew,
        'message': _('Auto-renewal {} successfully').format(
            _('enabled') if current_subscription.auto_renew else _('disabled')
        )
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """Cancel user's current subscription"""
    current_subscription = SubscriptionService.get_current_subscription(request.user)
    
    if not current_subscription:
        return Response({
            'success': False,
            'message': _('No active subscription found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    current_subscription.cancel()
    
    logger.info(f"User {request.user.username} canceled subscription {current_subscription.id}")
    
    return Response({
        'success': True,
        'message': _('Subscription canceled successfully')
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_ad_creation(request):
    """Check if user can create a new ad"""
    can_create, error_message = SubscriptionService.can_create_ad(request.user.id)
    limits = SubscriptionService.get_ads_limits(request.user.id)
    
    data = {
        'can_create': can_create,
        'error_message': error_message,
        'current_ads': limits['current'],
        'ads_limit': limits['limit'],
        'plan_name': limits['plan_name']
    }
    
    serializer = AdCreationCheckSerializer(data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def subscription_usage(request):
    """Get subscription usage details"""
    current_subscription = SubscriptionService.get_current_subscription(request.user)
    
    if not current_subscription:
        return Response({
            'message': _('No active subscription found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        usage = current_subscription.usage
        serializer = SubscriptionUsageSerializer(usage)
        return Response(serializer.data)
    except SubscriptionUsage.DoesNotExist:
        return Response({
            'message': _('Usage data not found')
        }, status=status.HTTP_404_NOT_FOUND)

# Admin-only views
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def subscription_stats(request):
    """Get subscription statistics (admin only)"""
    stats = SubscriptionService.get_subscription_stats()
    serializer = SubscriptionStatsSerializer(stats)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_create_subscription(request, user_id):
    """Create subscription for any user (admin only)"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = get_object_or_404(User, id=user_id)
    serializer = CreateSubscriptionSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                plan = get_object_or_404(SubscriptionPlan, id=serializer.validated_data['plan_id'])
                
                subscription = SubscriptionService.create_subscription(
                    user=user,
                    plan=plan,
                    payment_reference=serializer.validated_data.get('payment_reference'),
                    auto_renew=serializer.validated_data.get('auto_renew', False)
                )
                
                response_serializer = UserSubscriptionSerializer(subscription)
                
                logger.info(f"Admin {request.user.username} created subscription {subscription.id} for user {user.username}")
                
                return Response({
                    'success': True,
                    'message': _('Subscription created successfully'),
                    'subscription': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating subscription for user {user.username}: {e}")
            return Response({
                'success': False,
                'message': _('Error creating subscription'),
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'message': _('Invalid data'),
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_extend_subscription(request, subscription_id):
    """Extend subscription by specified days (admin only)"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id)
    days = request.data.get('days', 30)
    
    try:
        days = int(days)
        if days <= 0:
            return Response({
                'success': False,
                'message': _('Days must be a positive number')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.extend(days)
        
        logger.info(f"Admin {request.user.username} extended subscription {subscription.id} by {days} days")
        
        return Response({
            'success': True,
            'message': _('Subscription extended by {} days').format(days),
            'new_end_date': subscription.end_date
        })
        
    except ValueError:
        return Response({
            'success': False,
            'message': _('Invalid number of days')
        }, status=status.HTTP_400_BAD_REQUEST)
