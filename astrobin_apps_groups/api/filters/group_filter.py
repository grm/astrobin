from django.db import models
from django_filters import IsoDateTimeFilter
from rest_framework.filters import FilterSet

from astrobin_apps_groups.models import Group
from common.filters.list_filter import ListFilter


class GroupFilter(FilterSet):
    id = ListFilter(name="id", lookup_expr='in')
    ids = ListFilter(name="id", lookup_expr='in')
    member = ListFilter(name="members", lookup_expr='in')
    members = ListFilter(name="members", lookup_expr='in')

    class Meta:
        model = Group
        fields = {
            'id': (),
            'ids': (),
            'member': (),
            'members': (),
            'date_created': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'date_updated': ('lt', 'lte', 'exact', 'gt', 'gte'),
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
