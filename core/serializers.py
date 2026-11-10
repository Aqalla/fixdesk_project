from rest_framework import serializers
from .models import User, Location, Category, Ticket, Attachment, Comment, TicketHistory


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']
        read_only_fields = ['id', 'role']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        user.role = 'requester'
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'building', 'room']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file']

    def validate_file(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Размер файла не должен превышать 5 МБ')
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'text', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class TicketHistorySerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = TicketHistory
        fields = ['id', 'actor', 'old_status', 'new_status', 'note', 'created_at']
        read_only_fields = ['id', 'actor', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    history = TicketHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'author', 'assignee', 'location', 'category',
            'created_at', 'resolved_at', 'attachments', 'comments', 'history'
        ]
        read_only_fields = ['id', 'author', 'status', 'created_at', 'resolved_at']


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'location', 'category']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'priority', 'status',
            'author', 'assignee', 'location', 'category', 'created_at'
        ]


class AssignSerializer(serializers.Serializer):
    assignee = serializers.IntegerField()
    priority = serializers.ChoiceField(choices=Ticket.PRIORITY_CHOICES)


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5)


class ResolveSerializer(serializers.Serializer):
    result = serializers.CharField(required=True, min_length=5)


class ReopenSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5)


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['ticket'] = self.context['ticket']
        return super().create(validated_data)
