from django.db import models
from django.contrib.auth.models import User

class DiaryEntry(models.Model):
    MOOD_CHOICES = [
        ('happy', '😊 Χαρούμενος'),
        ('sad', '😢 Λυπημένος'),
        ('stressed', '😰 Αγχωμένος'),
        ('calm', '😌 Ήρεμος'),
        ('angry', '😠 Θυμωμένος'),
    ]

    TAG_CHOICES = [
        ('work', 'Εργασία'),
        ('health', 'Υγεία'),
        ('relationships', 'Σχέσεις'),
        ('personal', 'Προσωπικά'),
        ('other', 'Άλλο'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)


    # --- Νέα πεδία ---
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True, null=True)
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, blank=True, null=True)
    is_public = models.BooleanField(default=False)
    image = models.ImageField(upload_to='diary_images/', blank=True, null=True)
    image_base64 = models.TextField(blank=True, null=True)

    # π.χ. {"proud": true, "helped_someone": false}
    highlights = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class JournalAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    question_number = models.PositiveSmallIntegerField()
    answer = models.TextField()

    class Meta:
        unique_together = ('user', 'date', 'question_number')

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')


class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('danger', 'Danger'),
    ]

    ICON_CHOICES = [
        ('bell', 'Bell'),
        ('check-circle-fill', 'Check'),
        ('folder', 'Folder'),
        ('question-circle', 'Question'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, default='bell')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"
