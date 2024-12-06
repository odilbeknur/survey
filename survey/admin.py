from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Survey)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Response)
admin.site.register(Answer)
admin.site.register(DependentAnswer)


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at')
    search_fields = ('title', 'description')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'survey')
    list_filter = ('survey', 'question_type')
    search_fields = ('text',)

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question')



class AnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question', 'text_answer']

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0  # Не добавлять пустые строки для новых записей

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'survey', 'created_at')  # Отображать ID, опрос и дату создания
    inlines = [AnswerInline] 