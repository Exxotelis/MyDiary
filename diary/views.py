from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import DiaryEntry, UserBadge
from datetime import datetime
import random
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render
from .prompts_loader import get_daily_prompt
from .models import JournalAnswer
from django.utils import timezone
from datetime import date
from django.utils.timezone import now
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from datetime import timedelta
from django.conf import settings
from reportlab.pdfbase.pdfmetrics import stringWidth
from django.shortcuts import get_object_or_404
from .utils import get_streak, check_seven_day_streak, convert_image_to_base64







JOURNAL_QUESTIONS = {
    1: "Πώς νιώθω σήμερα;",
    2: "Ποια ήταν η πιο δύσκολη στιγμή της ημέρας;",
    3: "Ποιο ήταν το μεγαλύτερό μου επίτευγμα σήμερα;"
}



@login_required
def index(request):
    today = timezone.now().date()

    # Απαντήσεις χρήστη για σήμερα (εμφάνιση φόρμας)
    answers = {
        ans.question_number: ans
        for ans in JournalAnswer.objects.filter(user=request.user, date=today)
    }

    streak = get_streak(request.user)

    # Αποθήκευση απαντήσεων POST
    if request.method == 'POST':
        for q_num in JOURNAL_QUESTIONS:
            content = request.POST.get(f'q{q_num}')
            if content:
                obj, created = JournalAnswer.objects.get_or_create(
                    user=request.user,
                    date=today,
                    question_number=q_num,
                    defaults={'answer': content}
                )
                if not created:
                    obj.answer = content
                    obj.save()
        return redirect('index')

    # Πρόσφατη δραστηριότητα (τελευταίες 7 ημέρες)
    labels = []
    answer_data = []
    for i in range(6, -1, -1):  # 7 τελευταίες ημέρες (π.χ. 29/04 έως σήμερα)
        day = today - timedelta(days=i)
        labels.append(day.strftime('%d/%m'))
        count = JournalAnswer.objects.filter(user=request.user, date=day).count()
        answer_data.append(count)

    return render(request, 'diary/index.html', {
        'questions': JOURNAL_QUESTIONS,
        'answers': answers,
        'prompt': get_daily_prompt(),
        'streak': streak,
        'labels': labels,
        'answer_data': answer_data,
        'today': today,
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('calendar_view')
    else:
        form = UserCreationForm()
    return render(request, 'diary/register.html', {'form': form})


@login_required
def diary_events(request):
    entries = DiaryEntry.objects.filter(user=request.user, is_deleted=False)
    answers = JournalAnswer.objects.filter(user=request.user)

    answered_dates = set(answers.values_list('date', flat=True))

    data = []

    for entry in entries:
        highlights = entry.highlights or {}

        color = '#6c757d'
        if highlights.get('proud'):
            color = '#198754'
        elif highlights.get('had_difficult_time'):
            color = '#dc3545'
        elif highlights.get('helped'):
            color = '#0d6efd'

        data.append({
            'title': '📓 Καταχώρηση',
            'start': str(entry.date),
            'url': f'/entry/{entry.date}/',
            'color': color,
        })

    for date in answered_dates:
        data.append({
            'title': '🧠 Ημερήσιες Απαντήσεις',
            'start': str(date),
            'url': f'/answers/{date}/',
            'color': '#ffc107',
        })

    return JsonResponse(data, safe=False)




@login_required
def calendar(request):
    today = timezone.now().date()
    return render(request, 'diary/calendar.html', {'today': today})



@login_required
def my_entries_view(request):
    today = timezone.now().date()
    query = request.GET.get('q', '')
    entries = DiaryEntry.objects.filter(user=request.user, is_deleted=False).order_by('-date')


    if query:
        entries = entries.filter(content__icontains=query)

    entries = entries.order_by('-date')

    # Φορτώνουμε τις απαντήσεις του χρήστη και τις οργανώνουμε ανά ημερομηνία
    answers_by_date = {}
    answers = JournalAnswer.objects.filter(user=request.user)
    for ans in answers:
        answers_by_date.setdefault(str(ans.date), []).append(ans)



    return render(request, 'diary/my_entries.html', {
        'entries': entries,
        'answers_by_date': answers_by_date,
        'query': query
    })




@login_required
def entry_view(request, date):
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()

    entry, created = DiaryEntry.objects.get_or_create(
        user=request.user,
        date=date_obj,
        defaults={'is_deleted': False}
    )

    if entry.is_deleted:
        raise Http404("Αυτή η καταχώρηση βρίσκεται στον Κάδο.")

    prompt_seed = int(date_obj.strftime("%Y%m%d"))
    random.seed(prompt_seed)
    prompt = get_daily_prompt()

    if request.method == 'POST':
        # Βασικά πεδία
        entry.content = request.POST.get('content')
        entry.mood = request.POST.get('mood')
        entry.tag = request.POST.get('tag')
        entry.is_public = 'is_public' in request.POST
        entry.highlights = {
            'proud': 'highlight_proud' in request.POST,
            'helped': 'highlight_helped' in request.POST,
            'had_difficult_time': 'highlight_difficult' in request.POST,
        }

        # Διαγραφή εικόνας αν ζητήθηκε
        if request.POST.get('remove_image') == 'true':
            entry.image = None
            entry.image_base64 = None

        # Νέα εικόνα (μόνο αν δεν ζητήθηκε διαγραφή)
        elif request.FILES.get('image'):
            image_file = request.FILES['image']
            entry.image_base64 = convert_image_to_base64(image_file)
            entry.image = None  # Δεν χρησιμοποιούμε αρχεία σε production

        entry.save()

        # Badges και ειδοποιήσεις
        if DiaryEntry.objects.filter(user=request.user, is_deleted=False).count() == 1:
            messages.success(request, "🏅 Σου απονεμήθηκε το badge: Πρώτη Καταχώρηση!")

        if check_seven_day_streak(request.user):
            messages.success(request, "🎉 Συγχαρητήρια! Έχεις καταγράψει τις απαντήσεις σου για 7 συνεχόμενες ημέρες!")

        if check_seven_day_streak(request.user):
            if not UserBadge.objects.filter(user=request.user, badge_type='7-day-streak').exists():
                UserBadge.objects.create(user=request.user, badge_type='7-day-streak')
                messages.success(request, "🏅 Νέο Badge: 7 ημέρες συνεχόμενης καταγραφής!")

        return redirect('calendar')

    return render(request, 'diary/entry_form.html', {
        'entry': entry,
        'date': date_obj,
        'prompt': prompt
    })

@login_required
def daily_answers_view(request, date):
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    answers = JournalAnswer.objects.filter(user=request.user, date=date_obj).order_by('question_number')

    # Παίρνουμε prompt με seed για συγκεκριμένη μέρα
    prompt_seed = int(date_obj.strftime("%Y%m%d"))
    random.seed(prompt_seed)
    prompt = get_daily_prompt()

    return render(request, 'diary/daily_answers.html', {
        'date': date_obj,
        'answers': answers,
        'prompt': prompt
    })


@login_required
def export_answers_txt(request, date):
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    answers = JournalAnswer.objects.filter(user=request.user, date=date_obj).order_by('question_number')

    content = f"MyDiary – Ημερήσιες Απαντήσεις για {date_obj}\n\n"
    for ans in answers:
        content += f"Ερώτηση {ans.question_number}:\n{ans.answer}\n\n"

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=answers_{date}.txt'
    return response


@login_required
def export_answers_pdf(request, date):
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    answers = JournalAnswer.objects.filter(user=request.user, date=date_obj).order_by('question_number')

    # Δημιουργούμε PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Γραμματοσειρά με υποστήριξη ελληνικών
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('GreekFont', font_path))
    p.setFont("GreekFont", 14)

    y = height - 60
    p.drawString(50, y, f"MyDiary – Ημερήσιες Απαντήσεις για {date_obj}")
    y -= 30

    p.setFont("GreekFont", 12)

    for ans in answers:
        question = f"Ερώτηση {ans.question_number}:"
        p.drawString(50, y, question)
        y -= 20

        # Manual word-wrap για απάντηση
        max_width = width - 100  # 50px padding δεξιά/αριστερά
        lines = []
        for paragraph in ans.answer.splitlines():
            words = paragraph.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if stringWidth(test_line, "GreekFont", 12) < max_width:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

        for wrapped_line in lines:
            p.drawString(60, y, wrapped_line.strip())
            y -= 18

        y -= 10

        # Νέα σελίδα αν δεν χωράει
        if y < 100:
            p.showPage()
            p.setFont("GreekFont", 12)
            y = height - 60

    p.showPage()
    p.save()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="answers_{date}.pdf"'
    })

@login_required
def export_all_answers_pdf(request):
    answers = JournalAnswer.objects.filter(user=request.user).order_by('date', 'question_number')

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from io import BytesIO
    import os

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('GreekFont', font_path))
    p.setFont("GreekFont", 14)

    y = height - 60
    p.drawString(50, y, f"MyDiary – Όλες οι Ημερήσιες Απαντήσεις")
    y -= 30
    p.setFont("GreekFont", 12)

    for ans in answers:
        line_title = f"{ans.date} – Ερώτηση {ans.question_number}:"
        p.drawString(50, y, line_title)
        y -= 20

        max_width = width - 100
        lines = []
        for paragraph in ans.answer.splitlines():
            words = paragraph.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if stringWidth(test_line, "GreekFont", 12) < max_width:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

        for wrapped_line in lines:
            p.drawString(60, y, wrapped_line.strip())
            y -= 18
        y -= 10

        if y < 100:
            p.showPage()
            p.setFont("GreekFont", 12)
            y = height - 60

    p.showPage()
    p.save()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="all_journal_answers.pdf"'
    })

@login_required
def export_all_entries_pdf(request):
    entries = DiaryEntry.objects.filter(user=request.user).order_by('-date')

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from io import BytesIO
    import os

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('GreekFont', font_path))
    p.setFont("GreekFont", 14)

    y = height - 60
    p.drawString(50, y, f"MyDiary – Όλες οι Καταχωρήσεις")
    y -= 30
    p.setFont("GreekFont", 12)

    for entry in entries:
        p.drawString(50, y, f"📅 {entry.date}")
        y -= 20

        if entry.mood:
            p.drawString(60, y, f"Διάθεση: {entry.get_mood_display()}")
            y -= 18
        if entry.tag:
            p.drawString(60, y, f"Ετικέτα: {entry.get_tag_display()}")
            y -= 18

        if entry.content:
            lines = []
            words = entry.content.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if stringWidth(test_line, "GreekFont", 12) < width - 100:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

            for l in lines:
                p.drawString(60, y, l.strip())
                y -= 18

        y -= 20

        if y < 100:
            p.showPage()
            p.setFont("GreekFont", 12)
            y = height - 60

    p.showPage()
    p.save()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="all_diary_entries.pdf"'
    })



@login_required
def delete_entry(request, date):
    if request.method == 'POST':
        entry = get_object_or_404(DiaryEntry, user=request.user, date=date)
        entry.is_deleted = True
        entry.save()
        return redirect('my_entries')

@login_required
def trash_view(request):
    trashed_entries = DiaryEntry.objects.filter(user=request.user, is_deleted=True).order_by('-date')
    return render(request, 'diary/trash.html', {'entries': trashed_entries})

@login_required
def restore_entry(request, date):
    entry = get_object_or_404(DiaryEntry, user=request.user, date=date, is_deleted=True)
    entry.is_deleted = False
    entry.save()
    return redirect('trash')

@login_required
def permanent_delete_entry(request, date):

    entry = get_object_or_404(DiaryEntry, user=request.user, date=date, is_deleted=True)
    entry.delete()
    return redirect('trash')


def test(request):
    return render(request, 'diary/test.html')




@login_required
def export_today_answers_pdf(request):
    entries = DiaryEntry.objects.filter(user=request.user).order_by('-date')

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from io import BytesIO
    import os

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('GreekFont', font_path))
    p.setFont("GreekFont", 14)

    y = height - 60
    p.drawString(50, y, f"MyDiary – Όλες οι Καταχωρήσεις")
    y -= 30
    p.setFont("GreekFont", 12)

    for entry in entries:
        p.drawString(50, y, f"📅 {entry.date}")
        y -= 20

        if entry.mood:
            p.drawString(60, y, f"Διάθεση: {entry.get_mood_display()}")
            y -= 18
        if entry.tag:
            p.drawString(60, y, f"Ετικέτα: {entry.get_tag_display()}")
            y -= 18

        if entry.content:
            lines = []
            words = entry.content.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if stringWidth(test_line, "GreekFont", 12) < width - 100:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)

            for l in lines:
                p.drawString(60, y, l.strip())
                y -= 18

        y -= 20

        if y < 100:
            p.showPage()
            p.setFont("GreekFont", 12)
            y = height - 60

    p.showPage()
    p.save()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="all_diary_entries.pdf"'
    })




@login_required
def gallery_view(request):
    images = DiaryEntry.objects.filter(user=request.user, image_base64__isnull=False).exclude(image_base64='').order_by('-date')
    return render(request, 'diary/gallery.html', {'images': [e.image_base64 for e in images]})



@login_required
def profile_view(request):
    user = request.user

    total_entries = DiaryEntry.objects.filter(user=user, is_deleted=False).count()
    total_answers = JournalAnswer.objects.filter(user=user).count()
    badges = UserBadge.objects.filter(user=user)

    return render(request, 'diary/profile.html', {
        'user': user,
        'total_entries': total_entries,
        'total_answers': total_answers,
        'badges': badges,
    })

# Στο views.py

from django.http import HttpResponse
from .models import DiaryEntry

@login_required
def clear_images(request):
    entries = DiaryEntry.objects.filter(user=request.user)
    for entry in entries:
        entry.image = None
        entry.image_base64 = None
        entry.save()
    return HttpResponse("Images cleared.")


from django.core.management import call_command

@login_required
def run_migrations(request):
    call_command('migrate', interactive=False)
    return HttpResponse("Migrations applied.")




