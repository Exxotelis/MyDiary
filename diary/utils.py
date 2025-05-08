from django.utils import timezone
from datetime import timedelta
from .models import DiaryEntry, JournalAnswer, Notification, UserBadge, Badge



def get_streak(user):
    today = timezone.now().date()
    streak = 0

    while True:
        check_date = today - timedelta(days=streak)
        if DiaryEntry.objects.filter(user=user, date=check_date, is_deleted=False).exists():
            streak += 1
        else:
            break

    return streak


def check_seven_day_streak(user):
    today = timezone.now().date()
    streak_count = 0

    for i in range(7):
        day = today - timedelta(days=i)
        if JournalAnswer.objects.filter(user=user, date=day).exists():
            streak_count += 1
        else:
            break

    return streak_count == 7



def create_notification(user, message, level='info', icon='bell'):
    Notification.objects.create(user=user, message=message, level=level, icon=icon)


def award_badge(user, badge_name):
    badge, created = Badge.objects.get_or_create(name=badge_name)
    UserBadge.objects.get_or_create(user=user, badge=badge)
    create_notification(user, f"You have been awarded the '{badge_name}' badge!", level='success', icon='check-circle-fill')

def get_user_badges(user):
    return UserBadge.objects.filter(user=user).select_related('badge').order_by('-awarded_at')
