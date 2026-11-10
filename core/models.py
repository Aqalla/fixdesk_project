from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator


class User(AbstractUser):
    ROLE_CHOICES = [
        ('requester', 'Заявитель'),
        ('dispatcher', 'Диспетчер'),
        ('executor', 'Исполнитель'),
        ('admin', 'Администратор'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='requester')

    class Meta:
        indexes = [
            models.Index(fields=['role']),
        ]


class Location(models.Model):
    building = models.CharField(max_length=50)
    room = models.CharField(max_length=50)

    class Meta:
        unique_together = ['building', 'room']
        indexes = [
            models.Index(fields=['building', 'room']),
        ]

    def __str__(self):
        return f'{self.building}, каб. {self.room}'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('assigned', 'Назначена'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решена'),
        ('closed', 'Закрыта'),
        ('rejected', 'Отклонена'),
    ]

    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='authored_tickets')
    assignee = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='assigned_tickets', null=True, blank=True
    )
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['assignee']),
            models.Index(fields=['category']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f'#{self.id} - {self.title}'


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.ImageField(
        upload_to='attachments/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )

    class Meta:
        indexes = [
            models.Index(fields=['ticket']),
        ]

    def __str__(self):
        return f'{self.ticket.id} - {self.file.name}'


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.ticket.id} - {self.author.username}'


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name='history')
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    old_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20, null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.ticket.id} - {self.actor.username}'
