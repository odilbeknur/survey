from django.shortcuts import render, redirect
from .models import Survey, Response, Answer, Question, Choice
from .forms import SurveyForm, QuestionForm, ChoiceForm, EditQuestionForm, EditChoiceForm
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect



def survey_list_view(request):
    surveys = Survey.objects.all()  
    questions  = Question.objects.all()  
    return render(request, 'survey_list.html', {'surveys': surveys, 'questions': questions})

def survey_view(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    if request.method == 'POST':
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            response = Response.objects.create(survey=survey)
            for question in survey.questions.all():
                answer_data = form.cleaned_data.get(f'question_{question.id}')
                if question.question_type == 'text':
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=answer_data
                    )
                elif question.question_type in ['radio', 'select']:
                    choice = question.choices.get(id=answer_data)
                    Answer.objects.create(
                        response=response,
                        question=question,
                        choice=choice
                    )
                elif question.question_type == 'checkbox':
                    for choice_id in answer_data:
                        choice = question.choices.get(id=choice_id)
                        Answer.objects.create(
                            response=response,
                            question=question,
                            choice=choice
                        )
            return redirect('survey:thank_you')
    else:
        form = SurveyForm(survey=survey)
    return render(request, 'survey.html', {'form': form, 'survey': survey})

def thank_you_view(request):
    return render(request, 'thank_you.html')

def add_question_view(request):
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save() 
            for i in range(int(request.POST.get('choice_count', 0))):
                choice_text = request.POST.get(f'choice_{i}')
                if choice_text:
                    Choice.objects.create(question=question, text=choice_text)
            return redirect('survey:survey_list')  
    else:
        question_form = QuestionForm()

    return render(request, 'add_question.html', {'question_form': question_form})

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
                if question.question_type == 'text':
                    row[question.id] = answer.text_answer
                elif question.question_type in ['radio', 'select']:
                    row[question.id] = answer.choice.text if answer.choice else ''
                elif question.question_type == 'checkbox':
                    choices = Answer.objects.filter(response=response, question=question).values_list('choice__text', flat=True)
                    row[question.id] = ', '.join(choices)
                else:
                    row[question.id] = ''
            else:
                row[question.id] = ''  
        table_data.append(row)

    return render(request, 'survey_responses_table.html', {
        'survey': survey,
        'questions': questions,
        'table_data': table_data,
    })

def edit_question_view(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    choices = Choice.objects.filter(question=question)

    if request.method == 'POST':
        question_form = EditQuestionForm(request.POST, instance=question)
        choice_forms = [
            EditChoiceForm(request.POST, prefix=f'choice_{choice.id}', instance=choice)
            for choice in choices
        ]

        if question_form.is_valid() and all([cf.is_valid() for cf in choice_forms]):
            question_form.save()

            for cf in choice_forms:
                cf.save()

            delete_choices = request.POST.getlist('delete_choice')
            Choice.objects.filter(id__in=delete_choices).delete()

            new_choices = request.POST.getlist('new_choice')
            for new_choice_text in new_choices:
                if new_choice_text.strip():
                    Choice.objects.create(question=question, text=new_choice_text.strip())

            return redirect('survey:survey_list')  

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


def edit_survey_view(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)

    if request.method == 'POST':
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            return redirect('survey:survey_list')  # Перенаправление на список опросов
    else:
        # Передаем только survey
        form = SurveyForm(survey=survey)

    return render(request, 'edit_survey.html', {'form': form, 'survey': survey})