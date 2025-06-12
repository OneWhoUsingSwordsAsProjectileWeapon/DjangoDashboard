
# Subscription Management Module

This module provides comprehensive subscription management for the rental platform, including plan management, usage tracking, and automatic renewals.

## Features

- **Subscription Plans**: Flexible plan system with different tiers and limits
- **Usage Tracking**: Real-time tracking of user's ad creation and limits
- **Automatic Renewals**: Support for auto-renewal with notifications
- **Admin Management**: Full CRUD operations for plans and subscriptions
- **API Integration**: RESTful API for all subscription operations
- **Notifications**: Automated notifications for expiring subscriptions

## Models

### SubscriptionPlan
- Defines available subscription tiers
- Configurable pricing, duration, and limits
- Support for featured ads and premium features

### UserSubscription
- Links users to subscription plans
- Tracks subscription status and duration
- Supports auto-renewal functionality

### SubscriptionUsage
- Real-time tracking of plan usage
- Automatic updates when listings are created/deleted
- Provides usage statistics and limits

### SubscriptionLog
- Audit trail for all subscription events
- Tracks plan changes, renewals, and cancellations

## API Endpoints

### User Endpoints

#### Get Subscription Status
```
GET /api/subscriptions/status/
```
Returns current subscription status and usage information.

#### Get Available Plans
```
GET /api/subscriptions/api/plans/
```
Returns list of all available subscription plans.

#### Create Subscription
```
POST /api/subscriptions/create/
{
    "plan_id": 1,
    "auto_renew": true
}
```

#### Check Ad Creation Ability
```
GET /api/subscriptions/check-ad-creation/
```
Returns whether user can create a new ad.

#### Toggle Auto-Renewal
```
POST /api/subscriptions/toggle-auto-renew/
```

#### Cancel Subscription
```
POST /api/subscriptions/cancel/
```

### Admin Endpoints

#### Get Subscription Statistics
```
GET /api/subscriptions/admin/stats/
```

#### Create Subscription for User
```
POST /api/subscriptions/admin/create/<user_id>/
```

#### Extend Subscription
```
POST /api/subscriptions/admin/extend/<subscription_id>/
{
    "days": 30
}
```

## Services

### SubscriptionService
Core service providing:
- `can_create_ad(user_id)` - Check if user can create ads
- `get_ads_limits(user_id)` - Get current usage and limits
- `create_subscription(user, plan, ...)` - Create new subscription
- `get_subscription_stats()` - Get statistics for admin

### NotificationService
Handles subscription notifications:
- Expiration warnings (3 days before)
- Renewal success/failure notifications
- Automatic notification scheduling

## Integration with Listings

The module automatically integrates with the listings app:
- **Pre-creation Check**: Validates subscription before allowing ad creation
- **Usage Updates**: Automatically tracks when ads are created/deleted
- **Limit Enforcement**: Prevents creation when limits are reached

## Management Commands

### Setup Default Plans
```bash
python manage.py setup_default_plans
```
Creates default subscription plans and settings.

### Process Renewals
```bash
python manage.py process_subscription_renewals
```
Processes auto-renewals and sends notifications. Should be run daily via cron.

## Configuration

### Default Settings
- `free_ads_limit`: Number of ads free users can create (default: 2)
- `grace_period_days`: Grace period after subscription expires (default: 3)
- `notification_days_before_expiry`: When to send expiration warnings (default: 3)

## Admin Interface

The admin interface provides:
- **Plan Management**: Create and edit subscription plans
- **Subscription Overview**: View all user subscriptions with status
- **Usage Monitoring**: Track user usage against limits
- **Bulk Actions**: Activate, cancel, or extend multiple subscriptions
- **Audit Logs**: Complete history of subscription events

## Security Features

- **Admin-only Actions**: Sensitive operations require admin permissions
- **User Isolation**: Users can only access their own subscription data
- **Audit Trail**: All actions are logged for security and debugging
- **Rate Limiting**: API endpoints include appropriate rate limiting

## Localization

The module supports full internationalization with translatable strings for:
- Error messages
- Notification content
- Admin interface
- API responses

## Testing

The module includes comprehensive tests for:
- Subscription creation and management
- Usage tracking and limits
- Auto-renewal processing
- API endpoints
- Permission checks

## Monitoring and Analytics

Built-in analytics provide insights into:
- Subscription conversion rates
- Usage patterns
- Revenue by plan
- Churn analysis
- Plan popularity metrics
