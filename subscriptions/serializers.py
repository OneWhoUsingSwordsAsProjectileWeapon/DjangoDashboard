from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, SubscriptionUsage
from django.utils.translation import gettext as _
import uuid


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'plan_type', 'description',
            'price', 'currency', 'duration_days', 'ads_limit',
            'featured_ads_limit', 'premium_features', 'is_popular'
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    plan = SubscriptionPlanSerializer(read_only=True)
    days_remaining = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'status', 'start_date', 'end_date',
            'auto_renew', 'amount_paid', 'days_remaining',
            'is_active', 'created_at'
        ]


class SubscriptionUsageSerializer(serializers.ModelSerializer):
    """Serializer for subscription usage"""

    class Meta:
        model = SubscriptionUsage
        fields = [
            'ads_count', 'featured_ads_count', 'total_ads_created',
            'last_ad_created', 'updated_at'
        ]


class SubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for subscription status response"""
    has_subscription = serializers.BooleanField()
    plan_name = serializers.CharField(allow_blank=True, allow_null=True)
    subscription_status = serializers.CharField()
    current_ads = serializers.IntegerField()
    ads_limit = serializers.IntegerField()
    expires_at = serializers.DateTimeField(allow_null=True)
    days_remaining = serializers.IntegerField(allow_null=True)
    usage_percentage = serializers.FloatField(allow_null=True)


class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for creating subscriptions"""
    plan_id = serializers.IntegerField()
    auto_renew = serializers.BooleanField(default=False)
    payment_reference = serializers.CharField(required=False, allow_blank=True)

    def validate_plan_id(self, value):
        try:
            SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or inactive plan"))
        return value


class AdCreationCheckSerializer(serializers.Serializer):
    """Serializer for ad creation check response"""
    can_create = serializers.BooleanField()
    error_message = serializers.CharField(allow_blank=True)
    current_ads = serializers.IntegerField()
    ads_limit = serializers.IntegerField()
    plan_name = serializers.CharField()


class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics"""
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    plans_distribution = serializers.DictField()