import re
from typing import List, Union

from django.db.models import QuerySet
from django.urls import reverse

from astrobin.models import ImageRevision, Image
from astrobin_apps_platesolving.models import Solution, PlateSolvingAdvancedSettings


class SolutionService:
    solution = None  # type: Solution

    @staticmethod
    def get_or_create_advanced_settings(target: Union[Image, ImageRevision]) -> (PlateSolvingAdvancedSettings, bool):
        if target._meta.model_name == 'image':
            images = Image.objects_including_wip.filter(user=target.user).order_by('-pk')  # type: QuerySet[Image]
            for image in images:
                if image.solution and image.solution.advanced_settings:
                    latest_settings = image.solution.advanced_settings  # type: PlateSolvingAdvancedSettings
                    latest_settings.pk = None
                    latest_settings.sample_raw_frame_file = None
                    latest_settings.save()
                    return latest_settings, False
        elif target.image.solution and target.image.solution.advanced_settings:
            latest_settings = target.image.solution.advanced_settings
            latest_settings.pk = None
            latest_settings.save()
            return latest_settings, False

        return PlateSolvingAdvancedSettings.objects.create(), True

    def __init__(self, solution):
        # type: (Solution) -> None

        self.solution = solution

    def get_objects_in_field(self, clean=True) -> List[str]:
        objects = []

        if self.solution and self.solution.objects_in_field:
            objects = [x.strip() for x in self.solution.objects_in_field.split(',')]
        if self.solution and self.solution.advanced_annotations:
            advanced_annotations_lines = self.solution.advanced_annotations.split('\n')
            for line in advanced_annotations_lines:
                header = line.split(',')[0]

                if header != "Label":
                    continue

                advanced_annotation = line.split(',')[-1]

                if clean:
                    regex = r"^(?P<catalog>M|NGC|IC|LDN|LBN|PGC)(?P<id>\d+)$"
                    matches = re.findall(regex, advanced_annotation)
                    if len(matches) == 1:
                        catalog = matches[0][0]
                        number = matches[0][1]
                        advanced_annotation = "%s %s" % (catalog, number)

                if advanced_annotation.lower() not in [x.lower() for x in objects] and advanced_annotation != '':
                    objects.append(advanced_annotation)

        return sorted(objects)

    def duplicate_objects_in_field_by_catalog_space(self) -> List[str]:
        value = []
        objects = self.get_objects_in_field()
        space_regex = r"^(?P<catalog>M|NGC|IC|PGC|LDN|LBN|PGC) (?P<id>\d+)$"
        dash_regex = r"^(?P<catalog>Sh2|TYC)(?P<id>.*)$"

        for obj in objects:
            space_matches = re.findall(space_regex, obj)
            dash_matches = re.findall(dash_regex, obj)

            if len(space_matches) >= 1 or len(dash_matches) >= 1:
                if len(space_matches) >= 1:
                    catalog = space_matches[0][0]
                    number = space_matches[0][1]
                    value.append(f'{catalog}{number}')
                    value.append(f'{catalog} {number}')
                elif len(dash_matches) >= 1:
                    value.append(obj)
                    value.append(obj.replace('-', '_'))
            else:
                value.append(obj)

        return sorted(value)

    def get_search_query_around(self, degrees: int) -> str:
        def _wrap_angle(angle, min_angle, max_angle):
            range_size = max_angle - min_angle
            return (angle - min_angle) % range_size + min_angle

        ra = float(self.solution.advanced_ra or self.solution.ra)
        dec = float(self.solution.advanced_dec or self.solution.dec)

        ra_min = ra - degrees * 0.5
        ra_max = ra + degrees * 0.5

        if ra_min < 0:
            ra_min += 360
        elif ra_min > 360:
            ra_min -= 360

        if ra_max > 360:
            ra_max -= 360
        elif ra_max < 0:
            ra_max += 360

        dec_min = max(dec - degrees * 0.5, -90)
        dec_max = min(dec + degrees * 0.5, 90)

        field_min = 0
        field_max = degrees

        base_search_url = reverse('haystack_search')

        url_params = [
            "q=&d=i&t=all",
            "coord_ra_min=%.2f" % ra_min,
            "coord_ra_max=%.2f" % ra_max,
            "coord_dec_min=%.2f" % dec_min,
            "coord_dec_max=%.2f" % dec_max,
            "field_radius_min=%.2f" % field_min,
            "field_radius_max=%.2f" % field_max
        ]

        return base_search_url + "?" + "&".join(url_params)
