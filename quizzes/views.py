from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from .models import Quiz, Attempt, Question, Choice
from .forms import QuizForm, QuestionForm, ChoiceForm
from account.models import Account


def quiz_list(request):
    search_query = request.GET.get('q', '')  # Get the search term from the request

    if search_query:
        # Filter quizzes based on the search term and sort them alphabetically
        quizzes = Quiz.objects.filter(title__icontains=search_query).order_by('title')
    else:
        # Get all quizzes and sort them alphabetically
        quizzes = Quiz.objects.all().order_by('title')

    quizzes_with_attempts = []
    for quiz in quizzes:
        attempt = Attempt.objects.filter(quiz=quiz, student=request.user).order_by('-date_attempted').first()
        quizzes_with_attempts.append((quiz, attempt))

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes_with_attempts': quizzes_with_attempts,
        'search_query': search_query,
        'on_quizzes_page': True  # Add this line
    })




@login_required
def quiz_detail(request, quiz_title):
    quiz = get_object_or_404(Quiz, title=quiz_title)

    # Ensure that the user's account is correctly fetched
    user_account = Account.objects.get(email=request.user.email)

    if user_account.is_teacher:
        # For teachers: Show student attempts and scores
        student_attempts = Attempt.objects.filter(quiz=quiz).select_related('student')
        context = {'quiz': quiz, 'student_attempts': student_attempts}
        return render(request, 'quizzes/quiz_detail_teacher.html', context)
    else:
        # For students: Show quiz taking interface
        attempts = Attempt.objects.filter(quiz=quiz, student=request.user).count()
        context = {'quiz': quiz, 'attempts': attempts}

        if request.method == 'POST':
            if attempts < 3:
                score = 0
                for question in quiz.questions.all():
                    selected_choice = request.POST.get(f'question_{question.id}')
                    if selected_choice and question.choices.get(id=selected_choice).is_correct:
                        score += 1
                Attempt.objects.create(quiz=quiz, student=request.user, score=score)
                return redirect(reverse('quizzes:quiz_detail', args=(quiz.title,)))
            else:
                context['error'] = "You have already taken this quiz 3 times."
        else:
            # This part is for GET request, showing the quiz questions for the student to answer
            return render(request, 'quizzes/quiz_detail_student.html', context)

        # This return statement is for POST request, after the quiz is submitted
        return render(request, 'quizzes/quiz_detail_student.html', context)






@login_required
def create_quiz(request):
    if request.method == 'POST':
        quiz_form = QuizForm(request.POST)
        if quiz_form.is_valid():
            quiz = quiz_form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()

            # Process each question
            for i in range(0, 100):  # Assuming a maximum of 100 questions for safety
                question_text = request.POST.get(f'questions-{i}-text')
                if not question_text:
                    break  # Break if no more questions are found

                question = Question.objects.create(quiz=quiz, text=question_text)

                # Process each choice for the question
                for j in range(4):  # Assuming 4 choices per question
                    choice_text = request.POST.get(f'questions-{i}-choice-{j}')
                    correct_choice = request.POST.get(f'questions-{i}-correct')
                    if choice_text:
                        is_correct = False
                        if correct_choice.isdigit():
                            is_correct = (j + 1) == int(correct_choice)
                        Choice.objects.create(
                            question=question,
                            text=choice_text,
                            is_correct=is_correct
                        )

            return redirect('quizzes:quiz_list')
        else:
            return render(request, 'quizzes/create_quiz.html', {'quiz_form': quiz_form})
    else:
        quiz_form = QuizForm()

    return render(request, 'quizzes/create_quiz.html', {'quiz_form': quiz_form})