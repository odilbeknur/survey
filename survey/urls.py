from django.urls import path
from . import views

app_name = 'survey'

urlpatterns = [
    path('survey/<int:survey_id>/', views.survey_view, name='surveys'),
    path('surveys/', views.survey_list_view, name='survey_list'),
    path('thank_you/', views.thank_you_view, name='thank_you'),
    path('add-question/', views.add_question_view, name='add_question'),
    
    path('survey/<int:survey_id>/results/', views.survey_results_view, name='survey_results'),
    
    path('survey/<int:survey_id>/responses/', views.survey_responses_table, name='survey_responses_table'),
    path('question/<int:question_id>/edit/', views.edit_question_view, name='edit_question'),
    path('survey/<int:survey_id>/edit/', views.edit_survey_view, name='edit_survey'),
]
