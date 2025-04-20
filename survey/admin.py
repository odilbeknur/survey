from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Survey)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Response)
admin.site.register(Answer)


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'duration_minutes', 'created_at')
    search_fields = ('title', 'description')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'survey', 'required')
    list_filter = ('survey', 'question_type', 'required')
    search_fields = ('text',)

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'requires_comment')
    list_filter = ('question', 'is_correct')


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'choice', 'text_answer')
    list_filter = ('question',)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'survey', 'user_id', 'score', 'started_at', 'finished_at')
    list_filter = ('survey', 'finished_at')
    inlines = [AnswerInline]
