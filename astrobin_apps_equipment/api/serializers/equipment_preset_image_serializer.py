from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentPreset


class EquipmentPresetImageSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.create_thumbnail()
        return instance

    class Meta:
        model = EquipmentPreset
        fields = ['image_file']
