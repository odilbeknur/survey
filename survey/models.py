from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    topic = models.CharField(max_length=255, blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('survey:survey', args=[self.id])

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
    correct_text_answer = models.CharField(max_length=255, blank=True, null=True)
    case_sensitive = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse('survey:edit_question', args=[self.id])


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    requires_comment = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text or "Unnamed Choice"


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    employee_name = models.CharField(max_length=255)
    station_name = models.CharField(max_length=255, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    score = models.FloatField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee_name} - {self.survey.title} @ {self.started_at}"

    def evaluate(self):
        total_questions = self.survey.questions.count()
        correct_answers = 0

        for question in self.survey.questions.all():
            answers = self.answers.filter(question=question)
            print(f'\n[Вопрос #{question.id}] {question.text}')
            print(f'Тип вопроса: {question.question_type}')
            print(f'Ответы: {answers}')

            is_correct = False  # По умолчанию считаем, что ответ неправильный

            if question.question_type == 'checkbox':
                selected_texts = set(
                    answers.filter(choice__isnull=True).values_list('text_answer', flat=True)
                )
                correct_texts = set(
                    question.choices.filter(is_correct=True).values_list('text', flat=True)
                )
                print(f'Выбранные тексты: {selected_texts}')
                print(f'Правильные тексты: {correct_texts}')
                if selected_texts == correct_texts:
                    is_correct = True

            elif question.question_type in ['radio', 'select']:
                if answers.exists() and answers.first().choice and answers.first().choice.is_correct:
                    is_correct = True
                else:
                    print(f"Выбранный вариант: {answers.first().choice if answers.exists() else 'нет'}")

            elif question.question_type in ['text', 'textarea']:
                if answers.exists():
                    given = answers.first().text_answer or ""
                    expected = question.correct_text_answer or ""
                    if not question.case_sensitive:
                        given = given.lower()
                        expected = expected.lower()
                    print(f"Ожидалось: '{expected.strip()}', получено: '{given.strip()}'")
                    if given.strip() == expected.strip():
                        is_correct = True

            elif question.question_type == 'combo':
                if answers.exists():
                    answer = answers.first()
                    print(f"Выбран: {answer.choice}, комментарий: {answer.text_answer}")
                    if answer.choice and answer.choice.is_correct:
                        if not answer.choice.requires_comment or (answer.text_answer and answer.text_answer.strip()):
                            is_correct = True

            if is_correct:
                correct_answers += 1
            else:
                print("❌ Ответ считается неправильным.")

        if total_questions > 0:
            self.score = round((correct_answers / total_questions) * 100, 2)
        else:
            self.score = 0

        self.passed = self.score >= 70
        print(f'\nИтоговый результат: {self.score}% — {"пройдено" if self.passed else "не пройдено"}')
        self.save()



class Answer(models.Model):
    session = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
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
