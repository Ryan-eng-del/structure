from rest_framework import serializers
from . import models

class AlgorithmsTaskListSerializer(serializers.ModelSerializer):
    class Meta:
      model = models.AlgorithmTask
      fields = '__all__'
