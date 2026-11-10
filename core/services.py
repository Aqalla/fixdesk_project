from django.core.exceptions import ValidationError
from .models import Ticket, TicketHistory


VALID_TRANSITIONS = {
    'new': ['assigned', 'rejected'],
    'assigned': ['in_progress', 'rejected'],
    'in_progress': ['resolved'],
    'resolved': ['closed', 'in_progress'],
    'rejected': [],
    'closed': [],
}


def can_transition(ticket, new_status):
    old_status = ticket.status
    if old_status == new_status:
        return True
    allowed = VALID_TRANSITIONS.get(old_status, [])
    return new_status in allowed


def transition_status(ticket, new_status, actor, note=''):
    if not can_transition(ticket, new_status):
        raise ValidationError(
            f'Недопустимый переход статуса из {ticket.status} в {new_status}'
        )

    old_status = ticket.status
    ticket.status = new_status

    if new_status == 'resolved':
        from django.utils import timezone
        ticket.resolved_at = timezone.now()
    elif new_status == 'in_progress' and old_status == 'resolved':
        ticket.resolved_at = None

    ticket.save()

    TicketHistory.objects.create(
        ticket=ticket,
        actor=actor,
        old_status=old_status,
        new_status=new_status,
        note=note
    )

    return ticket


def record_assignment(ticket, assignee, priority, actor):
    old_status = ticket.status
    ticket.assignee = assignee
    ticket.priority = priority
    if ticket.status == 'new':
        ticket.status = 'assigned'
    ticket.save()

    TicketHistory.objects.create(
        ticket=ticket,
        actor=actor,
        old_status=old_status,
        new_status=ticket.status,
        note=f'Назначен: {assignee.username}, приоритет: {priority}'
    )

    return ticket
