import re
from enum import Enum
from functools import reduce
from typing import Any, Callable, Optional, Type, Union

from django.db.models import Q
from haystack.backends import SQ
from haystack.inputs import BaseInput, Clean
from operator import and_, or_

from haystack.query import SearchQuerySet

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin_apps_equipment.models.sensor_base_model import ColorOrMono


class MatchType(Enum):
    ALL = 'ALL'
    ANY = 'ANY'


class CustomContain(BaseInput):
    """
    An input type for making wildcard matches.
    """
    input_type_name = 'custom_contain'

    def prepare(self, query_obj):
        query_string = super(CustomContain, self).prepare(query_obj)
        try:
            query_string = query_string.decode('utf-8')
        except AttributeError:
            pass
        query_string = query_obj.clean(query_string)

        exact_bits = [Clean(bit).prepare(query_obj) for bit in query_string.split(' ') if bit]
        query_string = ' '.join(exact_bits)

        return '*{}*'.format(query_string)


class SearchService:
    @staticmethod
    def get_boolean_filter_value(value: Optional[Union[str, bool]]) -> Optional[int]:
        if value is None:
            return None

        if (
                value is True or
                isinstance(value, str) and (
                value.upper() == 'Y' or
                value == '1' or
                value.lower() == 'true'
        )
        ):
            return 1
        elif (
                value is False or
                isinstance(value, str) and (
                        value.upper() == 'N'
                        or value == '0'
                        or value.lower() == 'false'
                )
        ):
            return 0
        else:
            return None

    @staticmethod
    def apply_boolean_filter(
            data: dict, 
            results: SearchQuerySet,
            param_name: str,
            filter_attr: str
    ) -> SearchQuerySet:
        value = SearchService.get_boolean_filter_value(data.get(param_name))
        if value is None:
            return results
        return results.filter(**{filter_attr: value})

    @staticmethod
    def apply_range_filter(
            data: dict, 
            results: SearchQuerySet,
            param_name: str, 
            min_filter_attr: str,
            max_filter_attr: str = None,
            value_type: Type[Union[int, float, str]] = float,
            value_multiplier: Optional[Union[int, float, str]] = None
    ) -> SearchQuerySet:
        def get_adjusted_value(value: Union[int, float, str]) -> Optional[Union[int, float]]:
            try:
                adjusted_value = value_type(value)
                if value_multiplier is not None:
                    adjusted_value *= value_type(value_multiplier)
                return adjusted_value
            except (TypeError, ValueError):
                return None

        def apply_filter(value: Union[int, float, str], filter_attr: str, operator: str) -> SearchQuerySet:
            adjusted_value = get_adjusted_value(value)
            if adjusted_value is None or isinstance(adjusted_value, str) and adjusted_value == '':
                return results
            return results.filter(**{f'{filter_attr}{operator}': adjusted_value})

        if f'{param_name}_min' in data:
            results = apply_filter(data.get(f'{param_name}_min'), min_filter_attr, '__gte')

        if f'{param_name}_max' in data:
            results = apply_filter(data.get(f'{param_name}_max'), max_filter_attr, '__lte')

        if param_name in data:
            try:
                value = data.get(param_name)
                if isinstance(value, dict):
                    results = apply_filter(value.get('min'), min_filter_attr, '__gte')
                    results = apply_filter(value.get('max'), max_filter_attr, '__lte')
            except (TypeError, AttributeError):
                pass

        return results

    @staticmethod
    def apply_match_type_filter(
        data: dict,
        results: SearchQuerySet,
        key: str,
        match_type_key: str,
        query_func: Callable[[Any], Q]
    ) -> SearchQuerySet:
        if isinstance(data.get(key), dict):
            values = data.get(key).get("value")
            match_type = data.get(key).get("matchType")
        else:
            values = data.get(key)
            match_type = data.get(match_type_key)

        if match_type == MatchType.ALL.value:
            op = and_
        else:
            op = or_

        if values is not None and values != "":
            if isinstance(values, str):
                values = values.split(',')

            queries = [query_func(value) for value in values]

            if queries:
                results = results.filter(reduce(op, queries))

        return results

    @staticmethod
    def filter_by_subject(data, results: SearchQuerySet) -> SearchQuerySet:
        subject = data.get("subject")
        q = data.get("q")

        if subject is not None and subject != "":
            if list(SearchService.find_catalog_subjects(subject)):
                results = SearchService.filter_by_subject_text(results, subject)
            else:
                results = results.filter(objects_in_field=CustomContain(subject))

        if q is not None and q != "":
            if list(SearchService.find_catalog_subjects(q)):
                results |= SearchService.filter_by_subject_text(results, q)

        return results

    @staticmethod
    def find_catalog_subjects(text: str):
        text = text \
            .lower() \
            .replace('sh2-', 'sh2_') \
            .replace('sh2 ', 'sh2_') \
            .replace('messier', 'm') \
            .replace('"', '') \
            .replace("'", '') \
            .strip()

        pattern = r"(?P<catalog>Messier|M|NGC|IC|PGC|LDN|LBN|SH2_)\s?(?P<id>\d+)"
        return re.finditer(pattern, text, re.IGNORECASE)

    @staticmethod
    def filter_by_subject_text(results: SearchQuerySet, text: str) -> SearchQuerySet:
        if text is not None and text != "":
            catalog_entries = []
            matches = SearchService.find_catalog_subjects(text)

            for matchNum, match in enumerate(matches, start=1):
                groups = match.groups()
                catalog_entries.append("%s %s" % (groups[0], groups[1]))

            for entry in catalog_entries:
                results = results.narrow(f'objects_in_field:"{entry}"')

        return results

    @staticmethod
    def filter_by_telescope(data, results: SearchQuerySet) -> SearchQuerySet:
        telescope = data.get("telescope")

        if not telescope:
            return results

        try:
            telescope_id = int(telescope)
        except (ValueError, TypeError):
            telescope_id = None

        if isinstance(telescope, dict):
            telescope_id = telescope.get("id")
            telescope = telescope.get("name")

        if telescope_id and telescope_id != "":
            return results.filter(imaging_telescopes_2_id=telescope_id)

        if telescope and telescope != "":
            return results.filter(
                SQ(imaging_telescopes=CustomContain(telescope)) |
                SQ(imaging_telescopes_2=CustomContain(telescope))
            )

        return results

    @staticmethod
    def filter_by_camera(data, results: SearchQuerySet) -> SearchQuerySet:
        camera = data.get("camera")

        if not camera:
            return results

        try:
            camera_id = int(camera)
        except (ValueError, TypeError):
            camera_id = None

        if isinstance(camera, dict):
            camera_id = camera.get("id")
            camera = camera.get("name")

        if camera_id and camera_id != "":
            return results.filter(imaging_cameras_2_id=camera_id)

        if camera and camera != "":
            return results.filter(
                SQ(imaging_cameras=CustomContain(camera)) |
                SQ(imaging_cameras_2=CustomContain(camera))
            )

        return results

    @staticmethod
    def filter_by_telescope_type(data, results: SearchQuerySet) -> SearchQuerySet:
        telescope_type = data.get("telescope_type")

        if telescope_type is not None and telescope_type != "":
            types = telescope_type.split(',')
            results = results.filter(telescope_types__in=types)

        return results

    @staticmethod
    def filter_by_camera_type(data, results: SearchQuerySet) -> SearchQuerySet:
        camera_type = data.get("camera_type")

        if camera_type is not None and camera_type != "":
            types = camera_type.split(',')
            results = results.filter(camera_types__in=types)

        return results

    @staticmethod
    def filter_by_acquisition_months(data, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(month):
            return Q(acquisition_months=month)

        return SearchService.apply_match_type_filter(
            data,
            results,
            "acquisition_months",
            "acquisition_months_op",
            query_func
        )

    @staticmethod
    def filter_by_filter_types(data: dict, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(filter_type):
            return Q(filter_types=filter_type)

        return SearchService.apply_match_type_filter(
            data,
            results,
            "filter_types",
            "filter_types_op",
            query_func
        )

    @staticmethod
    def filter_by_color_or_mono(data, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(value):
            if value == ColorOrMono.COLOR.value:
                return Q(has_color_camera=True)
            elif value == ColorOrMono.MONO.value:
                return Q(has_mono_camera=True)
            return Q()

        return SearchService.apply_match_type_filter(
            data,
            results,
            "color_or_mono",
            "color_or_mono_op",
            query_func
        )

    @staticmethod
    def filter_by_remote_source(data, results: SearchQuerySet) -> SearchQuerySet:
        remote_source = data.get("remote_source")

        if remote_source is not None and remote_source != "":
            results = results.filter(remote_source=remote_source)

        return results

    @staticmethod
    def filter_by_subject_type(data, results: SearchQuerySet) -> SearchQuerySet:
        subject_type = data.get("subject_type")

        if subject_type in list(vars(SubjectType).keys()):
            results = results.filter(subject_type_char=subject_type)
        elif subject_type in list(vars(SolarSystemSubject).keys()):
            results = results.filter(solar_system_main_subject_char=subject_type)

        return results

    @staticmethod
    def filter_by_modified_camera(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_boolean_filter(data, results, "modified_camera", "has_modified_camera")

    @staticmethod
    def filter_by_animated(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_boolean_filter(data, results, "animated", "animated")

    @staticmethod
    def filter_by_video(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_boolean_filter(data, results, "video", "video")

    @staticmethod
    def filter_by_award(data, results: SearchQuerySet) -> SearchQuerySet:
        award = data.get("award")

        queries = []

        if award is not None and award != "":
            if isinstance(award, str):
                types = award.split(',')
            else:
                types = award

            if "iotd" in types:
                queries.append(Q(is_iotd=True))

            if "top-pick" in types:
                queries.append(Q(is_top_pick=True))

            if "top-pick-nomination" in types:
                queries.append(Q(is_top_pick_nomination=True))

        if len(queries) > 0:
            results = results.filter(reduce(or_, queries))

        return results

    @staticmethod
    def filter_by_country(data, results: SearchQuerySet) -> SearchQuerySet:
        country = data.get("country")

        if country is not None and country != "":
            results = results.filter(countries=CustomContain('__%s__' % country))

        return results

    @staticmethod
    def filter_by_data_source(data, results: SearchQuerySet) -> SearchQuerySet:
        data_source = data.get("data_source")

        if data_source is not None and data_source != "":
            results = results.filter(data_source=data_source)

        return results

    @staticmethod
    def filter_by_minimum_data(data, results: SearchQuerySet) -> SearchQuerySet:
        minimum_data = data.get("minimum_data")

        if minimum_data is not None and minimum_data != "":
            if isinstance(minimum_data, str):
                minimum = minimum_data.split(',')
            else:
                minimum = minimum_data

            for data in minimum:
                if data == 't':
                    results = results.exclude(SQ(_missing_="imaging_telescopes") & SQ(_missing_="imaging_telescopes_2"))
                if data == "c":
                    results = results.exclude(SQ(_missing_="imaging_cameras") & SQ(_missing_="imaging_cameras_2"))
                if data == "a":
                    results = results.exclude(_missing_="first_acquisition_date")
                if data == "s":
                    results = results.exclude(_missing_="pixel_scale")

        return results

    @staticmethod
    def filter_by_constellation(data, results: SearchQuerySet) -> SearchQuerySet:
        constellation = data.get("constellation")

        if constellation is not None and constellation != "":
            results = results.filter(constellation="__%s__" % constellation)

        return results

    @staticmethod
    def filter_by_bortle_scale(data, results: SearchQuerySet) -> SearchQuerySet:
        if 'bortle_scale_min' in data:
            try:
                minimum = float(data.get('bortle_scale_min'))
                results = results.filter(bortle_scale__gte=minimum)
            except TypeError:
                return results

        if 'bortle_scale_max' in data:
            try:
                maximum = float(data.get('bortle_scale_max'))
                results = results.filter(bortle_scale__lte=maximum)
            except TypeError:
                return results

        if 'bortle_scale' in data:
            try:
                value = data.get('bortle_scale')
                minimum = float(value.get('min'))
                maximum = float(value.get('max'))
                results = results.filter(bortle_scale__gte=minimum, bortle_scale__lte=maximum)
            except (TypeError, AttributeError):
                return results

        return results

    @staticmethod
    def filter_by_license(data, results: SearchQuerySet) -> SearchQuerySet:
        licenses = data.get("license")

        if licenses is not None and licenses != "":
            if isinstance(licenses, str):
                licenses = license.split(',')
            results = results.filter(license_name__in=licenses)

        return results

    @staticmethod
    def filter_by_camera_pixel_size(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'camera_pixel_size',
            'min_camera_pixel_size',
            'max_camera_pixel_size'
        )
    
    @staticmethod
    def filter_by_field_radius(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'field_radius',
            'field_radius',
            'field_radius'
        )

    @staticmethod
    def filter_by_pixel_scale(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'pixel_scale',
            'pixel_scale',
            'pixel_scale'
        )

    @staticmethod
    def filter_by_telescope_diameter(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'telescope_diameter',
            'min_aperture',
            'max_aperture',
            int
        )

    @staticmethod
    def filter_by_telescope_weight(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'telescope_weight',
            'min_telescope_weight',
            'max_telescope_weight'
        )

    @staticmethod
    def filter_by_mount_weight(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'mount_weight',
            'min_mount_weight',
            'max_mount_weight'
        )

    @staticmethod
    def filter_by_mount_max_payload(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'mount_max_payload',
            'min_mount_max_payload',
            'max_mount_max_payload'
        )

    @staticmethod
    def filter_by_telescope_focal_length(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'telescope_focal_length',
            'min_focal_length',
            'max_focal_length',
            int
        )

    @staticmethod
    def filter_by_integration_time(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'integration_time',
            'integration',
            'integration',
            value_multiplier=3600
        )

    @staticmethod
    def filter_by_size(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'size',
            'size',
            'size',
            int,
            value_multiplier=1e6
        )

    @staticmethod
    def filter_by_date_published(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'date_published',
            'published',
            'published',
            str
        )

    @staticmethod
    def filter_by_date_acquired(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'date_acquired',
            'last_acquisition_date',
            'last_acquisition_date',
            str
        )

    @staticmethod
    def filter_by_acquisition_type(data, results: SearchQuerySet) -> SearchQuerySet:
        acquisition_type = data.get("acquisition_type")

        if acquisition_type is not None and acquisition_type != "":
            results = results.filter(acquisition_type=acquisition_type)

        return results

    @staticmethod
    def filter_by_moon_phase(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'moon_phase',
            'moon_phase',
            'moon_phase'
        )
