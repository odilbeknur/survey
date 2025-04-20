from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('survey:surveys', args=[self.id])

    def get_results_url(self):
        return reverse('survey:survey_results', args=[self.id])

    def edit_absolute_url(self):
        return reverse('survey:edit_survey', args=[self.id])


class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Текстовый ответ'),
        ('textarea', 'Расширенный ответ'),
        ('radio', 'Один вариант ответа'),
        ('checkbox', 'Множественный выбор'),
        ('select', 'Выпадающий список'),
        ('combo', 'Комбинированный (Да/Нет + Текст)')
    ]
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    required = models.BooleanField(default=True)
    is_unique = models.BooleanField(default=False) 

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse('survey:edit_question', args=[self.id])



class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    requires_comment = models.BooleanField(default=False)

    def __str__(self):
        # Ensure the __str__ method always returns a string
        return self.text or "Unnamed Choice"


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to survey '{self.survey.title}' on {self.created_at}"


class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)  
    text_answer = models.TextField(null=True, blank=True)  

    def __str__(self):
        if self.choice:
            return f"Answer: {self.choice.text}"
        if self.text_answer:
            return f"Answer: {self.text_answer}"
        return "No answer provided"

    def clean(self):
        super().clean()

        if self.question.is_unique and self.text_answer:
            if Answer.objects.filter(
                question=self.question, 
                text_answer__iexact=self.text_answer  
            ).exclude(id=self.id).exists():
                raise ValidationError(f"'{self.text_answer}' уже существует для этого вопроса.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


