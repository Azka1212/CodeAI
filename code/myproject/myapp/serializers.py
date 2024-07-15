from rest_framework import serializers
from .models import APICall

class APICallSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICall
        fields = '__all__'
