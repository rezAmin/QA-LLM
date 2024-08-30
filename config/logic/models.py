from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=[('general', 'General'), ('specific', 'Specific')])
    title = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    date_asked = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question_text


class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    date_answered = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer_text
