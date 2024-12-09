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

@login_required
def survey_list_view(request):
    surveys = Survey.objects.all()  
    questions  = Question.objects.all()  
    return render(request, 'survey_list.html', {'surveys': surveys, 'questions': questions})

def survey_view(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    errors = {}  
    answers_to_save = []  
    has_errors = False  

    # Check if the user already submitted this survey
    last_submission_time = request.session.get(f'survey_{survey_id}_last_submission', None)
    if last_submission_time:
        last_submission_time = timezone.datetime.fromisoformat(last_submission_time)
        time_diff = timezone.now() - last_submission_time
        if time_diff < timedelta(minutes=5):
            # minutes_left = 5 - time_diff.total_seconds() // 60
            messages.info(request, f'Вы уже заполняли форму. Спасибо за участие!')
            return redirect('survey:thank_you')  # Redirect to thank you page or custom message page

    if request.method == 'POST':
        for question in survey.questions.all():
            answer_data = request.POST.get(f'question_{question.id}')

            try:
                # Check for duplicate answers
                if question.is_unique and answer_data:
                    if question.question_type in ['text', 'combo', 'radio', 'select']:
                        duplicate_check = Answer.objects.filter(
                            question=question, 
                            text_answer=answer_data
                        )
                        if duplicate_check.exists():
                            raise ValidationError(f"'{answer_data}' такая запись уже существует.")

                # Prepare 'combo' type answers with choice + comment
                if question.question_type == 'combo' and answer_data:
                    choice = question.choices.get(id=answer_data)
                    comment = request.POST.get(f'comment_{question.id}_{answer_data}', '').strip()
                    formatted_answer = f"{choice.text}: {comment}" if comment else choice.text
                    answers_to_save.append({
                        'question': question,
                        'text_answer': formatted_answer,
                        'choice': None
                    })

                # Prepare text answers
                elif question.question_type in ['text', 'textarea'] and answer_data:
                    answers_to_save.append({
                        'question': question,
                        'text_answer': answer_data,
                        'choice': None
                    })

                # Prepare single-choice answers
                elif question.question_type in ['radio', 'select'] and answer_data:
                    choice = question.choices.get(id=answer_data)
                    answers_to_save.append({
                        'question': question,
                        'text_answer': None,
                        'choice': choice
                    })

                # Prepare multiple-choice answers
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
                # Capture validation error and continue to next question
                errors[question.id] = str(e)
                has_errors = True

        # If there are no errors, save all valid answers
        if not has_errors:
            response = Response.objects.create(survey=survey)  # Create the response only if no errors
            for answer in answers_to_save:
                Answer.objects.create(
                    response=response,
                    question=answer['question'],
                    text_answer=answer['text_answer'],
                    choice=answer['choice']
                )

            # Mark the survey as submitted and store the submission timestamp
            request.session[f'survey_{survey_id}_last_submission'] = timezone.now().isoformat()

            # Redirect to the thank you page
            return redirect('survey:thank_you')

    # Render the survey form with validation errors
    return render(request, 'survey.html', {'survey': survey, 'errors': errors})


def thank_you_view(request):
    return render(request, 'thank_you.html')

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

@login_required
def survey_responses_table(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    questions = Question.objects.filter(survey=survey).order_by('id')
    responses = Response.objects.filter(survey=survey).prefetch_related('answers__question', 'answers__choice')

    table_data = []
    for response in responses:
        row = {'response_id': response.id}
        answers = {answer.question.id: answer for answer in response.answers.all()}
        for question in questions:
            if question.id in answers:
                answer = answers[question.id]
                if question.question_type in ['text', 'textarea']:
                    row[question.id] = answer.text_answer
                elif question.question_type in ['radio', 'select']:
                    row[question.id] = answer.choice.text if answer.choice else ''
                elif question.question_type == 'checkbox':
                    choices = Answer.objects.filter(response=response, question=question).values_list('text_answer', flat=True)
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
            for new_choice_text in new_choices:
                if new_choice_text.strip():
                    Choice.objects.create(question=question, text=new_choice_text.strip(), requires_comment=False)

            return redirect('survey:survey_list')  # Перенаправление на список опросов
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

@login_required
def edit_survey_view(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)

    if request.method == 'POST':
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            return redirect('survey:survey_list') 
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'edit_survey.html', {'form': form, 'survey': survey})


def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404