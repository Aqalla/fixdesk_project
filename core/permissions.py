from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsDispatcherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['dispatcher', 'admin']


class IsExecutor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'executor'


class IsRequester(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'requester'


class IsTicketAuthorOrDispatcherOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['dispatcher', 'admin']:
            return True
        return obj.author == request.user


class IsTicketAssigneeOrDispatcherOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['dispatcher', 'admin']:
            return True
        return obj.assignee == request.user


class IsTicketAuthorOrAssigneeOrDispatcherOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['dispatcher', 'admin']:
            return True
        if obj.author == request.user:
            return True
        if obj.assignee == request.user:
            return True
        return False


class IsAttachmentAccessible(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        ticket = obj.ticket
        if request.user.role in ['dispatcher', 'admin']:
            return True
        if ticket.author == request.user:
            return True
        if ticket.assignee == request.user:
            return True
        return False
