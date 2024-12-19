from rest_framework import serializers
from .models import CustomUser, Role
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'full_name', 'avatar', 'bio', 
                 'is_online', 'last_seen', 'date_joined', 'role', 'email_verified')
        read_only_fields = ('id', 'date_joined', 'last_seen', 'is_online', 
                          'email_verified')
        
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'full_name', 'password', 'password2', 'bio')

    def validate(self, data):
        # Validate password match
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate password strength
        try:
            validate_password(data['password'])
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return data

    def create(self, validated_data):
        # Remove password2 from the data
        validated_data.pop('password2', None)
        
        # Create user instance
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        
        # Add optional fields
        if 'bio' in validated_data:
            user.bio = validated_data['bio']
            user.save()
            
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'full_name', 'bio', 'avatar', 'current_password', 'new_password')
        extra_kwargs = {
            'username': {'required': False},
            'full_name': {'required': False}
        }

    def validate(self, data):
        if 'new_password' in data and not data.get('current_password'):
            raise serializers.ValidationError(
                {"current_password": "Current password is required to set a new password."}
            )
        
        if 'current_password' in data and not data.get('new_password'):
            raise serializers.ValidationError(
                {"new_password": "New password is required when current password is provided."}
            )
            
        return data

    def update(self, instance, validated_data):
        # Handle password change if provided
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        
        if current_password and new_password:
            if not instance.check_password(current_password):
                raise serializers.ValidationError(
                    {"current_password": "Current password is incorrect."}
                )
            instance.set_password(new_password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance

