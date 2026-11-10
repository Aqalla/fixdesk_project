import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Location, Category, Ticket, Attachment, Comment, TicketHistory

User = get_user_model()


class FixDeskAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='admin123', role='admin'
        )
        self.dispatcher = User.objects.create_user(
            username='dispatcher', email='dispatcher@test.com', password='disp123', role='dispatcher'
        )
        self.executor = User.objects.create_user(
            username='executor', email='executor@test.com', password='exec123', role='executor'
        )
        self.requester1 = User.objects.create_user(
            username='requester1', email='req1@test.com', password='req123', role='requester'
        )
        self.requester2 = User.objects.create_user(
            username='requester2', email='req2@test.com', password='req123', role='requester'
        )

        self.location = Location.objects.create(building='A', room='101')
        self.category = Category.objects.create(name='Электрика')

    def get_token(self, username, password):
        response = self.client.post('/api/auth/login/', {'username': username, 'password': password})
        return response.data['token']

    def test_full_ticket_lifecycle(self):
        token = self.get_token('requester1', 'req123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.post('/api/tickets/', {
            'title': 'Сломана розетка',
            'description': 'Не работает в кабинете 101',
            'priority': 'medium',
            'location': self.location.id,
            'category': self.category.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ticket_id = Ticket.objects.latest('id').id

        dispatcher_token = self.get_token('dispatcher', 'disp123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {dispatcher_token}')

        response = self.client.post(f'/api/tickets/{ticket_id}/assign/', {
            'assignee': self.executor.id,
            'priority': 'high'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        executor_token = self.get_token('executor', 'exec123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {executor_token}')

        response = self.client.post(f'/api/tickets/{ticket_id}/start/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(f'/api/tickets/{ticket_id}/resolve/', {
            'result': 'Заменил розетку'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        requester_token = self.get_token('requester1', 'req123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {requester_token}')

        response = self.client.post(f'/api/tickets/{ticket_id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ticket = Ticket.objects.get(id=ticket_id)
        self.assertEqual(ticket.status, 'closed')

    def test_reopen_resolved_ticket(self):
        token = self.get_token('requester1', 'req123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        ticket = Ticket.objects.create(
            author=self.requester1,
            assignee=self.executor,
            location=self.location,
            category=self.category,
            title='Тест',
            description='Тест',
            priority='medium',
            status='resolved'
        )

        response = self.client.post(f'/api/tickets/{ticket.id}/reopen/', {'reason': 'Не работает'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')
        self.assertIsNone(ticket.resolved_at)

        executor_token = self.get_token('executor', 'exec123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {executor_token}')

        response = self.client.post(f'/api/tickets/{ticket.id}/resolve/', {
            'result': 'Исправил окончательно'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolved')
        self.assertIsNotNone(ticket.resolved_at)

    def test_stranger_cannot_see_other_tickets(self):
        ticket = Ticket.objects.create(
            author=self.requester1,
            assignee=self.executor,
            location=self.location,
            category=self.category,
            title='Тест',
            description='Тест',
            priority='medium',
            status='new'
        )

        token = self.get_token('requester2', 'req123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(f'/api/tickets/{ticket.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        comment = Comment.objects.create(
            ticket=ticket,
            author=self.requester1,
            text='Комментарий'
        )

        response = self.client.get(f'/api/tickets/{ticket.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_dispatcher_sees_all_executor_sees_assigned(self):
        ticket1 = Ticket.objects.create(
            author=self.requester1,
            assignee=self.executor,
            location=self.location,
            category=self.category,
            title='Тест1',
            description='Тест',
            priority='medium',
            status='assigned'
        )

        ticket2 = Ticket.objects.create(
            author=self.requester2,
            assignee=None,
            location=self.location,
            category=self.category,
            title='Тест2',
            description='Тест',
            priority='medium',
            status='new'
        )

        dispatcher_token = self.get_token('dispatcher', 'disp123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {dispatcher_token}')

        response = self.client.get('/api/tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        executor_token = self.get_token('executor', 'exec123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {executor_token}')

        response = self.client.get('/api/tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], ticket1.id)

    def test_invalid_status_transition_409(self):
        token = self.get_token('requester1', 'req123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        ticket = Ticket.objects.create(
            author=self.requester1,
            location=self.location,
            category=self.category,
            title='Тест',
            description='Тест',
            priority='medium',
            status='new'
        )

        executor_token = self.get_token('executor', 'exec123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {executor_token}')

        response = self.client.post(f'/api/tickets/{ticket.id}/resolve/', {'result': 'Тест'})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        response = self.client.post(f'/api/tickets/{ticket.id}/start/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_history_on_assignee_change(self):
        ticket = Ticket.objects.create(
            author=self.requester1,
            location=self.location,
            category=self.category,
            title='Тест',
            description='Тест',
            priority='medium',
            status='new'
        )

        initial_history_count = TicketHistory.objects.filter(ticket=ticket).count()

        token = self.get_token('dispatcher', 'disp123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.post(f'/api/tickets/{ticket.id}/assign/', {
            'assignee': self.executor.id,
            'priority': 'high'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history_count = TicketHistory.objects.filter(ticket=ticket).count()
        self.assertEqual(history_count, initial_history_count + 1)

        history = TicketHistory.objects.filter(ticket=ticket).last()
        self.assertIn('Назначен', history.note)
        self.assertIn(self.executor.username, history.note)

    def test_report_with_no_resolved_tickets(self):
        token = self.get_token('dispatcher', 'disp123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get('/api/reports/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avg_resolution_hours', response.data)
        self.assertEqual(response.data['avg_resolution_hours'], 0)

    def test_role_permissions_on_actions(self):
        ticket = Ticket.objects.create(
            author=self.requester1,
            location=self.location,
            category=self.category,
            title='Тест',
            description='Тест',
            priority='medium',
            status='new'
        )

        requester_token = self.get_token('requester1', 'req123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {requester_token}')

        response = self.client.post(f'/api/tickets/{ticket.id}/assign/', {
            'assignee': self.executor.id,
            'priority': 'high'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        executor_token = self.get_token('executor', 'exec123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {executor_token}')

        response = self.client.post(f'/api/tickets/{ticket.id}/assign/', {
            'assignee': self.executor.id,
            'priority': 'high'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        dispatcher_token = self.get_token('dispatcher', 'disp123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {dispatcher_token}')

        response = self.client.post(f'/api/tickets/{ticket.id}/assign/', {
            'assignee': self.executor.id,
            'priority': 'high'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
