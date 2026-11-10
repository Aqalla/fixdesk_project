from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Avg, Q

from .models import User, Location, Category, Ticket, Attachment, Comment
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    LocationSerializer, CategorySerializer,
    TicketSerializer, TicketCreateSerializer, TicketListSerializer,
    AssignSerializer, RejectSerializer, ResolveSerializer, ReopenSerializer,
    CommentSerializer, CommentCreateSerializer, AttachmentSerializer
)
from .permissions import (
    IsAdmin, IsDispatcherOrAdmin, IsExecutor,
    IsTicketAuthorOrDispatcherOrAdmin,
    IsTicketAssigneeOrDispatcherOrAdmin,
    IsTicketAuthorOrAssigneeOrDispatcherOrAdmin,
    IsAttachmentAccessible
)
from .services import transition_status, record_assignment


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            from django.contrib.auth import authenticate
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'user': UserSerializer(user).data,
                    'token': token.key
                })
            return Response(
                {'detail': 'Неверные учетные данные'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'detail': 'Выход выполнен'})
        except:
            return Response({'detail': 'Ошибка выхода'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            return Response(UserSerializer(request.user).data)
        elif request.method == 'PATCH':
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('author', 'assignee', 'location', 'category').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['location', 'category', 'assignee', 'priority', 'status']
    search_fields = ['id', 'title', 'description']

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        elif self.action == 'list':
            return TicketListSerializer
        return TicketSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['dispatcher', 'admin']:
            return super().get_queryset()
        elif user.role == 'executor':
            return super().get_queryset().filter(assignee=user)
        else:
            return super().get_queryset().filter(author=user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        user = request.user
        available_actions = []

        if user.role in ['dispatcher', 'admin']:
            if instance.status in ['new', 'assigned']:
                available_actions.append('assign')
            if instance.status in ['new', 'assigned']:
                available_actions.append('reject')
        elif user.role == 'executor':
            if instance.status == 'assigned' and instance.assignee == user:
                available_actions.append('start')
            if instance.status == 'in_progress' and instance.assignee == user:
                available_actions.append('resolve')
        elif user.role == 'requester':
            if instance.status == 'resolved' and instance.author == user:
                available_actions.extend(['confirm', 'reopen'])

        data['available_actions'] = available_actions
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[IsDispatcherOrAdmin])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        serializer = AssignSerializer(data=request.data)
        if serializer.is_valid():
            try:
                assignee = User.objects.get(id=serializer.validated_data['assignee'], role='executor')
                record_assignment(
                    ticket, assignee, serializer.validated_data['priority'], request.user
                )
                return Response({'detail': 'Исполнитель назначен'})
            except User.DoesNotExist:
                return Response(
                    {'assignee': 'Исполнитель не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsDispatcherOrAdmin])
    def reject(self, request, pk=None):
        ticket = self.get_object()
        serializer = RejectSerializer(data=request.data)
        if serializer.is_valid():
            try:
                transition_status(ticket, 'rejected', request.user, serializer.validated_data['reason'])
                return Response({'detail': 'Заявка отклонена'})
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsExecutor])
    def start(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assignee != request.user:
            return Response(
                {'detail': 'Вы не назначены на эту заявку'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            transition_status(ticket, 'in_progress', request.user)
            return Response({'detail': 'Заявка взята в работу'})
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=['post'], permission_classes=[IsExecutor])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        if ticket.assignee != request.user:
            return Response(
                {'detail': 'Вы не назначены на эту заявку'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ResolveSerializer(data=request.data)
        if serializer.is_valid():
            try:
                transition_status(ticket, 'resolved', request.user, serializer.validated_data['result'])
                return Response({'detail': 'Заявка решена'})
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request, pk=None):
        ticket = self.get_object()
        if ticket.author != request.user:
            return Response(
                {'detail': 'Только автор может подтвердить решение'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            transition_status(ticket, 'closed', request.user)
            return Response({'detail': 'Заявка закрыта'})
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reopen(self, request, pk=None):
        ticket = self.get_object()
        if ticket.author != request.user:
            return Response(
                {'detail': 'Только автор может вернуть заявку в работу'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ReopenSerializer(data=request.data)
        if serializer.is_valid():
            try:
                transition_status(ticket, 'in_progress', request.user, serializer.validated_data['reason'])
                return Response({'detail': 'Заявка возвращена в работу'})
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsTicketAuthorOrAssigneeOrDispatcherOrAdmin])
    def comments(self, request, pk=None):
        ticket = self.get_object()
        serializer = CommentCreateSerializer(
            data=request.data,
            context={'request': request, 'ticket': ticket}
        )
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, IsAttachmentAccessible]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        from django.http import FileResponse
        return FileResponse(instance.file.open('rb'))


class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsDispatcherOrAdmin]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        total = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status__in=['new', 'assigned', 'in_progress']).count()
        resolved_tickets = Ticket.objects.filter(status='resolved').count()
        closed_tickets = Ticket.objects.filter(status='closed').count()

        resolved_queryset = Ticket.objects.filter(
            status__in=['resolved', 'closed'],
            resolved_at__isnull=False
        )

        avg_hours = 0
        if resolved_queryset.exists():
            total_seconds = 0
            for ticket in resolved_queryset:
                delta = ticket.resolved_at - ticket.created_at
                total_seconds += delta.total_seconds()
            avg_hours = total_seconds / resolved_queryset.count() / 3600

        return Response({
            'total_tickets': total,
            'open_tickets': open_tickets,
            'resolved_tickets': resolved_tickets,
            'closed_tickets': closed_tickets,
            'avg_resolution_hours': round(avg_hours, 2) if avg_hours else 0
        })
