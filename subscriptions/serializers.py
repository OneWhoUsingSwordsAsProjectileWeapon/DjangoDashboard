
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import SubscriptionPlan, UserSubscription, SubscriptionUsage
from .services import SubscriptionService

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'plan_type', 'description',
            'price', 'currency', 'duration_days', 'ads_limit',
            'featured_ads_limit', 'premium_features', 'is_popular'
        ]
        read_only_fields = ['id', 'slug']

class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'plan_id', 'status', 'start_date', 'end_date',
            'auto_renew', 'amount_paid', 'is_active', 'days_remaining',
            'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'start_date', 'end_date', 'amount_paid', 'created_at'
        ]

class SubscriptionUsageSerializer(serializers.ModelSerializer):
    """Serializer for subscription usage"""
    plan_ads_limit = serializers.IntegerField(source='subscription.plan.ads_limit', read_only=True)
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionUsage
        fields = [
            'ads_count', 'featured_ads_count', 'plan_ads_limit',
            'plan_name', 'usage_percentage', 'total_ads_created',
            'last_ad_created'
        ]
        read_only_fields = '__all__'
    
    def get_usage_percentage(self, obj):
        if obj.subscription.plan.ads_limit == 0:
            return 0
        return round((obj.ads_count / obj.subscription.plan.ads_limit) * 100, 1)

class SubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for subscription status response"""
    has_subscription = serializers.BooleanField()
    plan_name = serializers.CharField(allow_null=True)
    subscription_status = serializers.CharField()
    current_ads = serializers.IntegerField()
    ads_limit = serializers.IntegerField()
    expires_at = serializers.DateTimeField(allow_null=True)
    days_remaining = serializers.IntegerField(allow_null=True)
    usage_percentage = serializers.FloatField(allow_null=True)

class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for creating a subscription"""
    plan_id = serializers.IntegerField()
    auto_renew = serializers.BooleanField(default=False)
    payment_reference = serializers.UUIDField(required=False)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or inactive subscription plan"))

class AdCreationCheckSerializer(serializers.Serializer):
    """Serializer for ad creation check response"""
    can_create = serializers.BooleanField()
    error_message = serializers.CharField(allow_blank=True)
    current_ads = serializers.IntegerField()
    ads_limit = serializers.IntegerField()
    plan_name = serializers.CharField()

class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics (admin only)"""
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()
    expiring_soon = serializers.IntegerField()
    plan_stats = serializers.ListField()
