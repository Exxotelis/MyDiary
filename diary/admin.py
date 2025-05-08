from django.contrib import admin
from .models import DiaryEntry
from .models import DiaryEntry, JournalAnswer, Badge, UserBadge, Notification, UserProfile, ProfileImage

@admin.register(JournalAnswer)
class JournalAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'question_number', 'short_answer')
    list_filter = ('date', 'question_number')
    search_fields = ('answer',)

    def short_answer(self, obj):
        return obj.answer[:50] + '...' if len(obj.answer) > 50 else obj.answer
    short_answer.short_description = 'Απάντηση'

@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'mood', 'tag', 'is_public')
    list_filter = ('mood', 'tag', 'is_public')
    search_fields = ('content',)
    date_hierarchy = 'date'

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'level', 'timestamp')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_image')

@admin.register(ProfileImage)
class ProfileImageAdmin(admin.ModelAdmin):
    list_display = ('user', 'image_url', 'is_active', 'uploaded_at')