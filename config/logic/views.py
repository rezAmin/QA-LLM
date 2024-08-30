from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import pandas as pd
import os
import json
import requests
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from django.conf import settings

from .models import Answer, Question

tokenizer = AutoTokenizer.from_pretrained("SajjadAyoubi/xlm-roberta-large-fa-qa")
model = AutoModelForQuestionAnswering.from_pretrained("SajjadAyoubi/xlm-roberta-large-fa-qa")

def load_dataframe():
    csv_path = os.path.join(settings.BASE_DIR, 'concat.csv')
    return pd.read_csv(csv_path)

@login_required
def home(request):
    df = load_dataframe()
    titles = df['title'].unique()
    user = request.user if request.user.is_authenticated else None

    questions = Question.objects.filter(user=user).order_by('-answer__date_answered')

    questions_with_answers = []
    for question in questions:
        answer = Answer.objects.filter(question=question).first()
        questions_with_answers.append({
            'id': question.id,
            'text': question.question_text,
            'answer': answer.answer_text if answer else 'بدون پاسخ',
            'date_asked': question.date_asked.strftime('%Y-%m-%d %H:%M:%S'),
            'date_answered': answer.date_answered.strftime('%Y-%m-%d %H:%M:%S') if answer else 'بدون پاسخ'
        })

    return render(request, 'logic/home.html', {
        'titles': titles,
        'user': user,
        'questions_with_answers': questions_with_answers
    })


@csrf_exempt
def get_content(request):
    if request.method == 'GET':
        title = request.GET.get('title')
        df = load_dataframe()
        try:
            row = df[df['title'] == title].iloc[0]
            content = row['content']

            context = {
                'title': row['title'],
                'lead': row['lead'],
                'content': content
            }
            return JsonResponse(context)
        except IndexError:
            return JsonResponse({"error": "عنوان یافت نشد"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=405)


def find_answer_in_context(context, question):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    inputs = tokenizer(question, context, return_tensors='pt', max_length=512, truncation=True).to(device)
    model.to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    start = torch.argmax(outputs.start_logits)
    end = torch.argmax(outputs.end_logits) + 1

    answer_tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'][0][start:end])
    answer = tokenizer.convert_tokens_to_string(answer_tokens).strip()
    answer = answer.replace('<s>', '').replace('</s>', '').strip()
    answer = ' '.join(answer.split())

    if not answer:
        answer = "پاسخ خوبی پیدا نکردم"

    return answer

@csrf_exempt
@login_required
def ask_question(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question_type = data.get('question_type')
            title = data.get('title', '')
            question_text = data.get('question')
            keywords = data.get('keywords', [])
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not question_text:
            return JsonResponse({"error": "Question not provided"}, status=400)

        try:

            question = Question.objects.create(
                user=request.user,
                question_text=question_text,
                question_type=question_type,
                title=title,
                keywords=keywords
            )


            answer = Answer.objects.create(
                question=question,
                answer_text="در حال پردازش..."
            )

            if question_type == "general":
                colab_url = 'https://699d-35-240-149-177.ngrok-free.app/get_best_answer'
                try:
                    response = requests.post(colab_url, json={"question": question_text, "keywords": keywords})
                    response.raise_for_status()
                    print(response.json().get('best_answer'))
                    answer_text = response.json().get('best_answer', 'پاسخ مناسبی یافت نشد.')
                except requests.exceptions.Timeout:
                    answer_text = 'درخواست به دلیل تایم‌اوت با مشکل مواجه شد.'
                except requests.exceptions.RequestException as e:
                    answer_text = f'خطا در درخواست: {str(e)}'

            elif question_type == "specific":
                if not title:
                    return JsonResponse({"error": "Title not provided for specific question"}, status=400)

                df = load_dataframe()
                try:
                    context = df[df['title'] == title]['content'].iloc[0]
                except IndexError:
                    return JsonResponse({"error": "Title not found in the data"}, status=404)

                answer_text = find_answer_in_context(context, question_text)

            else:
                return JsonResponse({"error": "Invalid question type"}, status=400)


            answer.answer_text = answer_text
            answer.date_answered = timezone.now()
            answer.save()

            response_data = {
                'answer': answer_text,
                'date_answered': answer.date_answered.strftime('%Y-%m-%d %H:%M:%S'),
                'question_text': question_text,
                'date_asked': question.date_asked.strftime('%Y-%m-%d %H:%M:%S'),
                'question_id': question.id
            }

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required
def get_question_history(request):
    user = request.user
    questions = Question.objects.filter(user=user).order_by('-date_asked')
    questions_with_answers = []

    for question in questions:
        answer = Answer.objects.filter(question=question).first()
        questions_with_answers.append({
            'id': question.id,
            'text': question.question_text,
            'answer': answer.answer_text if answer else 'بدون پاسخ',
            'date_asked': question.date_asked.strftime('%Y-%m-%d %H:%M:%S'),
            'date_answered': answer.date_answered.strftime('%Y-%m-%d %H:%M:%S') if answer else 'بدون پاسخ'
        })

    return JsonResponse({'questions': questions_with_answers})


@login_required
def get_answer(request):
    question_id = request.GET.get('id')
    try:
        question = Question.objects.get(id=question_id)
        answer = Answer.objects.get(question=question)
        return JsonResponse({'answer': answer.answer_text if answer.answer_text else 'بدون پاسخ'})
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    except Answer.DoesNotExist:
        return JsonResponse({'answer': 'بدون پاسخ'})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'logic/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'logic/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return render(request, 'logic/logout.html')
