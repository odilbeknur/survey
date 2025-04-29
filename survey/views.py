import openpyxl
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Survey, Response, Answer, Question, Choice
from .forms import SurveyForm, QuestionForm, ChoiceForm, EditQuestionForm, EditChoiceForm
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests


# Отображение списка форм
@login_required
def survey_list_view(request):
    surveys = Survey.objects.all()  
    questions  = Question.objects.all()  
    return render(request, 'survey_list.html', {'surveys': surveys, 'questions': questions})


# Отображение формы по id
def survey_view(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    errors = {}
    answers_to_save = []
    has_errors = False

    if request.method == 'POST':
        print("Form submitted.")  # Добавляем лог, чтобы увидеть, когда форма отправляется
        for question in survey.questions.all():
            answer_data = request.POST.get(f'question_{question.id}')
            try:
                if question.is_unique and answer_data:
                    if question.question_type in ['text', 'combo', 'radio', 'select']:
                        duplicate_check = Answer.objects.filter(
                            question=question,
                            text_answer=answer_data
                        )
                        if duplicate_check.exists():
                            raise ValidationError(f"Ответ '{answer_data}' уже существует для этого вопроса.")

                if question.question_type == 'combo' and answer_data:
                    choice = question.choices.get(id=answer_data)
                    comment = request.POST.get(f'comment_{question.id}_{answer_data}', '').strip()
                    formatted_answer = f"{choice.text}: {comment}" if comment else choice.text
                    answers_to_save.append({
                        'question': question,
                        'text_answer': formatted_answer,
                        'choice': None
                    })

                elif question.question_type in ['text', 'textarea'] and answer_data:
                    answers_to_save.append({
                        'question': question,
                        'text_answer': answer_data,
                        'choice': None
                    })

                elif question.question_type in ['radio', 'select'] and answer_data:
                    choice = question.choices.get(id=answer_data)
                    answers_to_save.append({
                        'question': question,
                        'text_answer': None,
                        'choice': choice
                    })

                elif question.question_type == 'checkbox':
                    selected_choices = request.POST.getlist(f'question_{question.id}')
                    for choice_id in selected_choices:
                        choice = question.choices.get(id=choice_id)
                        comment = request.POST.get(f'comment_{choice_id}', '').strip()
                        formatted_answer = f"{choice.text}: {comment}" if comment else choice.text
                        answers_to_save.append({
                            'question': question,
                            'text_answer': formatted_answer,
                            'choice': None
                        })

            except ValidationError as e:
                errors[question.id] = str(e)
                has_errors = True

        if not has_errors:
            employee_name = request.session.get('employee_name') or "Неизвестный"
            survey_response = Response.objects.create(
                survey=survey,
                employee_name=employee_name,
                station_name=settings.STATION_NAME
            )

            for answer in answers_to_save:
                Answer.objects.create(
                    session=survey_response,
                    question=answer['question'],
                    text_answer=answer['text_answer'],
                    choice=answer['choice']
                )

            survey_response.evaluate()
            survey_response.finished_at = timezone.now()
            survey_response.save()

            return redirect('survey:thank_you')

    return render(request, 'survey.html', {'survey': survey, 'errors': errors})


# Страница после завершения теста
def thank_you_view(request):
    return render(request, 'thank_you.html')


# Добавление вопросов
@login_required
def add_question_view(request):
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save()  # Сохраняем вопрос
            
            # Добавляем варианты ответа
            for i in range(int(request.POST.get('choice_count', 0))):
                choice_text = request.POST.get(f'choice_{i}')
                if choice_text:
                    Choice.objects.create(question=question, text=choice_text)
            
            # Обрабатываем комбинированный вопрос
            if question.question_type == 'combo':  # Если это комбинированный вопрос
                Choice.objects.create(question=question, text='Да')  # Добавляем "Да"
                Choice.objects.create(question=question, text='Нет')  # Добавляем "Нет"
            
            return redirect('survey:survey_list')  # Перенаправляем на список опросов
    else:
        question_form = QuestionForm()

    return render(request, 'add_question.html', {'question_form': question_form})


# Отображение результатов и ответов теста
@login_required
def survey_results_view(request, survey_id):
    responses = Response.objects.filter(survey_id=survey_id).prefetch_related('answers__question')
    questions = Question.objects.filter(survey_id=survey_id)

    statistics = []
    for question in questions:
        if question.question_type in ['radio', 'checkbox', 'select']:
            stats = (
                Answer.objects.filter(question=question)
                .values('choice__text')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
        else:
            stats = Answer.objects.filter(question=question).values_list('text_answer', flat=True)
        statistics.append({'question': question, 'stats': stats})

    return render(request, 'survey_results.html', {
        'responses': responses,
        'statistics': statistics,
    })


# Таблица результатов
@login_required
def survey_responses_table(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    questions = Question.objects.filter(survey=survey).order_by('id')
    sessions = Response.objects.filter(survey=survey).prefetch_related('answers__question', 'answers__choice')

    table_data = []
    for session in sessions:
        row = {'session_id': session.id}
        answers = {answer.question.id: answer for answer in session.answers.all()}
        for question in questions:
            if question.id in answers:
                answer = answers[question.id]
                if question.question_type in ['text', 'textarea']:
                    row[question.id] = answer.text_answer
                elif question.question_type in ['radio', 'select']:
                    row[question.id] = answer.choice.text if answer.choice else ''
                elif question.question_type == 'checkbox':
                    choices = Answer.objects.filter(session=session, question=question).values_list('text_answer', flat=True)
                    row[question.id] = ', '.join(filter(None, choices))
                elif question.question_type == 'combo':
                    row[question.id] = answer.text_answer
                else:
                    row[question.id] = ''
            else:
                row[question.id] = ''
        table_data.append(row)

    # Excel file download logic
    if request.GET.get('download') == 'true':
        # Create an Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Survey Responses'

        # Create header row
        headers = ['ID Респондента'] + [question.text for question in questions]
        ws.append(headers)

        # Add rows for each response
        for row in table_data:
            ws.append([row['response_id']] + [row.get(question.id, '') for question in questions])

        # Prepare the HttpResponse to download the file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{survey.title}_responses.xlsx"'
        wb.save(response)
        return response

    return render(request, 'survey_responses_table.html', {
        'survey': survey,
        'questions': questions,
        'table_data': table_data,
    })

# Редактирование вопроса
@login_required
def edit_question_view(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    choices = Choice.objects.filter(question=question)

    if request.method == 'POST':
        question_form = EditQuestionForm(request.POST, instance=question)
        choice_forms = [
            EditChoiceForm(request.POST, prefix=f'choice_{choice.id}', instance=choice)
            for choice in choices
        ]

        if question_form.is_valid() and all(cf.is_valid() for cf in choice_forms):
            question_form.save()
            for cf in choice_forms:
                cf.save()

            # Обработка новых вариантов
            new_choices = request.POST.getlist('new_choice')
            for new_text in new_choices:
                new_text = new_text.strip()
                if new_text and not choices.filter(text=new_text).exists():
                    Choice.objects.create(
                        question=question,
                        text=new_text,
                        requires_comment=False
                    )

            return redirect('survey:survey_list')  # Измени на нужную тебе ссылку
    else:
        question_form = EditQuestionForm(instance=question)
        choice_forms = [
            EditChoiceForm(prefix=f'choice_{choice.id}', instance=choice)
            for choice in choices
        ]

    return render(request, 'edit_question.html', {
        'question_form': question_form,
        'choice_forms': choice_forms,
        'question': question,
    })

# Редактирование опросника (пока не нужно)
@login_required
def edit_survey_view(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)

    if request.method == 'POST':
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            # Здесь можно добавить обработку результатов, если нужно
            return redirect('survey:survey_list')  # Или на другую страницу, если нужно
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'edit_survey.html', {
        'form': form,
        'survey': survey,
    })


def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404


def select_employee_view(request):
    station_id = 1  # Возможно, этот ID станции будет динамическим
    org_units = []
    surveys = Survey.objects.all()

    # Подгрузка подразделений для станции
    try:
        url = f"http://127.0.0.1:8000/api/employees/org-units/{station_id}/"
        response = requests.get(url)
        response.raise_for_status()
        org_units = response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch organizational units: {e}")

    if request.method == 'POST':
        survey_id = request.POST.get('survey_id')
        employee_name = request.POST.get('employee_name')
        print("EMPLOYEE NAME",employee_name)
        # Проверка, что выбраны все необходимые данные
        if not survey_id or not employee_name:
            return render(request, 'select_employee.html', {
                'org_units': org_units,
                'surveys': surveys,
                'error': "Пожалуйста, выберите тест и сотрудника."
            })

        # Сохраняем данные в сессии
        request.session['employee_name'] = employee_name
        return redirect('survey:survey', survey_id=survey_id)

    return render(request, 'select_employee.html', {
        'org_units': org_units,
        'surveys': surveys
    })

def employees_by_orgunit_view(request):
    department_id = request.GET.get("org_unit")
    employees = []

    if department_id:
        url = f"http://127.0.0.1:8000/api/employees/by-department/{department_id}/"
        response = requests.get(url)
        employees = response.json()

    # Отправляем HTML с выбором сотрудников, чтобы HTMX мог его вставить
    return render(request, "_employee_select.html", {"employees": employees})