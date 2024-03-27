from rest_framework import serializers
from . import models

class AlgorithmsTaskListSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()
    def get_id(self, instance):
       return instance.id.hex[:10]
    
    class Meta:
      model = models.AlgorithmTask
      fields = '__all__'
