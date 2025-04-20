from django import forms
from .models import Survey, Response, Answer, Question, Choice

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        exam = kwargs.pop('exam', None)
        super().__init__(*args, **kwargs)

        if exam:
            for question in exam.questions.all():
                field_name = f'question_{question.id}'
                choices = [(choice.id, choice.text) for choice in question.choices.all()]

                match question.question_type:
                    case 'text':
                        self.fields[field_name] = forms.CharField(
                            label=question.text,
                            required=question.required,
                            widget=forms.TextInput(attrs={'class': 'form-control'}),
                        )
                    case 'textarea':
                        self.fields[field_name] = forms.CharField(
                            label=question.text,
                            required=question.required,
                            widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                        )
                    case 'radio':
                        self.fields[field_name] = forms.ChoiceField(
                            label=question.text,
                            required=question.required,
                            choices=choices,
                            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                        )
                    case 'checkbox':
                        self.fields[field_name] = forms.MultipleChoiceField(
                            label=question.text,
                            required=question.required,
                            choices=choices,
                            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                        )
                    case 'select':
                        self.fields[field_name] = forms.ChoiceField(
                            label=question.text,
                            required=question.required,
                            choices=choices,
                            widget=forms.Select(attrs={'class': 'form-select'}),
                        )
                    case 'combo':
                        self.fields[field_name] = forms.ChoiceField(
                            label=question.text,
                            required=question.required,
                            choices=choices,
                            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                        )
                        self.fields[f'comment_{question.id}'] = forms.CharField(
                            label=f"Комментарий к вопросу: {question.text}",
                            required=False,
                            widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
                        )



class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'exam',
            'text',
            'question_type',
            'required',
            'is_unique',
            'correct_text_answer',
            'case_sensitive',
        ]


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = [
            'text',
            'description',
            'requires_comment',
            'is_correct',
        ]


class EditQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text',
            'question_type',
            'required',
            'correct_text_answer',
            'case_sensitive',
        ]


class EditChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = [
            'text',
            'is_correct',
            'requires_comment',
            'description',
        ]
