
try:
    from django.core.exceptions import FieldDoesNotExist
except ImportError:
    from django.db.models.fields import FieldDoesNotExist

from django.core.exceptions import FieldError
from django.db import models as django_models

from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.managers import NestedIntervalsManager

def get_model_field_names(model_class):
    return tuple(field.name for field in model_class._meta.fields)

def register_fields(model_class, *field_names):
    model_class._nested_intervals_field_names = field_names
    for field_name in field_names:
        if field_name in get_model_field_names(model_class):
            raise FieldError("'{}' is already an existing model field.".format(field_name))

        django_models.PositiveIntegerField(default=0).contribute_to_class(model_class, field_name)
