from django import template
from quizzes.models import Attempt

register = template.Library()

@register.filter
def get_student_choice(attempt, question):
    return attempt.get_student_choice_for_question(question)
