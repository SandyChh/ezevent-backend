"""Accounts serializers."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Organizer, Attendee

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=["ORGANIZER", "ATTENDEE"])
    organisation_name = serializers.CharField(max_length=200, required=False, default="")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        org_name = validated_data.pop("organisation_name", "")
        role = validated_data["role"]
        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            password=validated_data["password"],
            role=role,
        )
        if role == "ORGANIZER":
            Organizer.objects.create(user=user, organisation_name=org_name)
        elif role == "ATTENDEE":
            Attendee.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "is_active", "created_at"]
        read_only_fields = fields
