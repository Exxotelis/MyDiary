from django.contrib import admin
from .models import DiaryEntry
from .models import DiaryEntry, JournalAnswer
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

