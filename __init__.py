from django.db import models as django_models
from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.managers import NestedIntervalsManager

def register_fields(model_class, *field_names):
    model_class._nested_intervals_field_names = field_names
    for field_name in field_names:
        django_models.PositiveIntegerField(default=0).contribute_to_class(model_class, field_name)
