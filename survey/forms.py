from django import forms
from .models import Survey, Response, Answer, Question, Choice

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey', None)  # Make 'survey' optional
        super().__init__(*args, **kwargs)
        if survey:
            for question in survey.questions.all():
                if question.question_type == 'text':
                    self.fields[f'question_{question.id}'] = forms.CharField(
                        label=question.text,
                        required=question.required,
                        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                    )
                elif question.question_type == 'radio':
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        label=question.text,
                        required=question.required,
                        choices=[(choice.id, choice.text) for choice in question.choices.all()],
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    )
                elif question.question_type == 'checkbox':
                    self.fields[f'question_{question.id}'] = forms.MultipleChoiceField(
                        label=question.text,
                        required=question.required,
                        choices=[(choice.id, choice.text) for choice in question.choices.all()],
                        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                    )
                elif question.question_type == 'select':
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        label=question.text,
                        required=question.required,
                        choices=[(choice.id, choice.text) for choice in question.choices.all()],
                        widget=forms.Select(attrs={'class': 'form-select'}),
                    )
                elif question.question_type == 'combo':
                    # Add the radio button field
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        label=question.text,
                        required=question.required,
                        choices=[(choice.id, choice.text) for choice in question.choices.all()],
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    )
                    # Add the optional comment field
                    self.fields[f'comment_{question.id}'] = forms.CharField(
                        label=f"Комментарий для: {question.text}",
                        required=False,
                        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
                    )



class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['survey', 'text', 'question_type', 'required']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'requires_comment', 'description']


class EditQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'required']

class EditChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text']