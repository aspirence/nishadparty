from django import template
from accounts.models import FeaturePermission

register = template.Library()


@register.filter(name='has_feature_permission')
def has_feature_permission(user, feature):
    """
    Template filter to check if user has a specific feature permission.
    Usage: {% if user|has_feature_permission:'ASSET_MANAGEMENT' %}
    """
    return FeaturePermission.user_has_permission(user, feature)


@register.filter(name='has_any_permission')
def has_any_permission(user):
    """
    Template filter to check if user has any active permissions.
    Usage: {% if user|has_any_permission %}
    """
    if user.user_type == 'ADMINISTRATOR':
        return True
    return FeaturePermission.objects.filter(user=user, is_active=True).exists()


@register.filter(name='get_user_features')
def get_user_features(user):
    """
    Template filter to get all features a user has access to.
    Usage: {% for feature in user|get_user_features %}
    """
    return FeaturePermission.get_user_features(user)
