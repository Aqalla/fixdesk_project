from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Location, Category, Ticket, Attachment, Comment
from PIL import Image
from io import BytesIO
import random
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for FixDesk'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        User.objects.all().delete()
        Location.objects.all().delete()
        Category.objects.all().delete()
        Ticket.objects.all().delete()

        admin = User.objects.create_superuser(
            username='admin',
            email='admin@fixdesk.local',
            password='admin123',
            role='admin',
            first_name='Админ',
            last_name='Админов'
        )

        dispatcher = User.objects.create_user(
            username='dispatcher',
            email='dispatcher@fixdesk.local',
            password='dispatcher123',
            role='dispatcher',
            first_name='Диспетчер',
            last_name='Диспетчеров'
        )

        executors = []
        for i in range(1, 4):
            executor = User.objects.create_user(
                username=f'executor{i}',
                email=f'executor{i}@fixdesk.local',
                password=f'executor{i}123',
                role='executor',
                first_name=f'Исполнитель{i}',
                last_name='Исполнительский'
            )
            executors.append(executor)

        requesters = []
        for i in range(1, 4):
            requester = User.objects.create_user(
                username=f'requester{i}',
                email=f'requester{i}@fixdesk.local',
                password=f'requester{i}123',
                role='requester',
                first_name=f'Заявитель{i}',
                last_name='Заявительский'
            )
            requesters.append(requester)

        buildings = ['А', 'Б', 'В']
        rooms = [101, 102, 201, 202, 301, 302]
        locations = []
        for building in buildings:
            for room in rooms:
                location = Location.objects.create(building=building, room=str(room))
                locations.append(location)

        categories = [
            Category.objects.create(name='Электрика'),
            Category.objects.create(name='Сантехника'),
            Category.objects.create(name='Мебель'),
            Category.objects.create(name='Климат'),
        ]

        titles = [
            'Не работает розетка',
            'Протекает кран',
            'Сломана стул',
            'Нет холода в аудитории',
            'Свет мигает',
            'Засор в раковине',
            'Дверь не закрывается',
            'Шумит кондиционер',
            'Отвалилась ножка стола',
            'Нет воды',
        ]

        statuses = ['new', 'assigned', 'in_progress', 'resolved', 'closed', 'rejected']
        priorities = ['low', 'medium', 'high']

        for i in range(25):
            ticket = Ticket.objects.create(
                author=random.choice(requesters),
                assignee=random.choice(executors) if random.random() > 0.3 else None,
                location=random.choice(locations),
                category=random.choice(categories),
                title=random.choice(titles),
                description=f'Описание проблемы для заявки #{i+1}. Требуется срочное вмешательство.',
                priority=random.choice(priorities),
                status=random.choice(statuses),
                created_at=timezone.now() - timezone.timedelta(days=random.randint(1, 30))
            )

            if ticket.status == 'resolved':
                ticket.resolved_at = ticket.created_at + timezone.timedelta(days=random.randint(1, 5))
                ticket.save()

            if random.random() > 0.5:
                for j in range(random.randint(1, 3)):
                    img = Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                    img_io = BytesIO()
                    img.save(img_io, 'JPEG')
                    img_io.seek(0)
                    from django.core.files.uploadedfile import SimpleUploadedFile
                    file = SimpleUploadedFile(f'photo_{j}.jpg', img_io.read(), content_type='image/jpeg')
                    Attachment.objects.create(ticket=ticket, file=file)

            if random.random() > 0.5:
                for j in range(random.randint(1, 3)):
                    Comment.objects.create(
                        ticket=ticket,
                        author=random.choice([admin, dispatcher] + executors + requesters),
                        text=f'Комментарий #{j+1} к заявке #{ticket.id}'
                    )

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Dispatcher: dispatcher / dispatcher123')
        self.stdout.write('Executor1: executor1 / executor1123')
        self.stdout.write('Executor2: executor2 / executor2123')
        self.stdout.write('Executor3: executor3 / executor3123')
        self.stdout.write('Requester1: requester1 / requester1123')
        self.stdout.write('Requester2: requester2 / requester2123')
        self.stdout.write('Requester3: requester3 / requester3123')
