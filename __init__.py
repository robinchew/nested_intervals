from django.db import models as django_models
from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.managers import NestedIntervalsManager

def register_fields(model_class):
    for field_name in model_class.nested_intervals_field_names:
        django_models.PositiveIntegerField(default=0).contribute_to_class(model_class, field_name)


def register_magic(model_class, name11, name12, name21, name22):
    model_class.nested_intervals_field_names = (name11, name12, name21, name22)
    register_fields(model_class)

    if not issubclass(model_class, NestedIntervalsModelMixin):
        # Inherit mixin magically
        bases = list(model_class.__bases__)
        bases.insert(0, NestedIntervalsModelMixin)
        model_class.__bases__ = tuple(bases)

    # Set manager magically
    NestedIntervalsManager().contribute_to_class(model_class, 'nested_intervals')
