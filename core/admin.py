from django.contrib import admin
from .models import User, Location, Category, Ticket, Attachment, Comment, TicketHistory


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['building', 'room']
    list_filter = ['building']
    search_fields = ['building', 'room']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'priority', 'author', 'assignee', 'created_at']
    list_filter = ['status', 'priority', 'category', 'location']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'resolved_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'file']
    list_filter = ['ticket']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'text', 'created_at']
    list_filter = ['ticket', 'created_at']
    search_fields = ['text']


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'actor', 'old_status', 'new_status', 'created_at']
    list_filter = ['ticket', 'created_at']
    readonly_fields = ['created_at']
