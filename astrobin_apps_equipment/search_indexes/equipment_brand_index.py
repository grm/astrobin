# noinspection PyMethodMayBeStatic
from typing import List

from django.db.models import Q
from haystack import fields
from haystack.constants import Indexable

from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_equipment.search_indexes.equipment_base_index import EquipmentBaseIndex

PREPARED_FIELD_CACHE_EXPIRATION = 60
PREPARED_IMAGES_CACHE_KEY = 'astrobin_apps_equipment_search_indexed_images_%s_%d'


class EquipmentBrandIndex(EquipmentBaseIndex, Indexable):
    # Number of users who have used this brand.
    equipment_brand_user_count = fields.IntegerField()

    # Number of images that feature this brand.
    equipment_brand_image_count = fields.IntegerField()

    def get_model(self):
        return EquipmentBrand

    def image_queryset(self, obj: EquipmentBrand) -> Q:
        return \
            Q(imaging_telescopes_2__brand=obj) | \
            Q(imaging_cameras_2__brand=obj) | \
            Q(mounts_2__brand=obj) | \
            Q(filters_2__brand=obj) | \
            Q(accessories_2__brand=obj) | \
            Q(software_2__brand=obj) | \
            Q(guiding_telescopes_2__brand=obj) | \
            Q(guiding_cameras_2__brand=obj)

    def prepare_equipment_brand_user_count(self, obj) -> int:
        return self._prepare_user_count(obj)

    def prepare_equipment_brand_image_count(self, obj) -> int:
        return self._prepare_image_count(obj)
