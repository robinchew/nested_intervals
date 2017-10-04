try:
    from django.core.exceptions import FieldDoesNotExist
except ImportError:
    from django.db.models.fields import FieldDoesNotExist

from django.core.exceptions import FieldError
from django.db import models as django_models

def get_model_field_names(model_class):
    return tuple(field.name for field in model_class._meta.fields)

def register_fields(model_class, *field_names, **kwargs):
    assert len(field_names) == 5, 'First 4 names are for nested intervals integer fields. The 5th name is a parent field.'
    model_class._nested_intervals_field_names = field_names

    # Register nested interval fields

    for field_name in field_names[0:-1]:
        if field_name in get_model_field_names(model_class):
            raise FieldError("'{}' is already an existing model field.".format(field_name))

        django_models.PositiveIntegerField().contribute_to_class(model_class, field_name)

    # Register parent field

    parent_field_name = field_names[-1]

    if parent_field_name in get_model_field_names(model_class):
        # If parent field already exists in Model, either
        # raise exception or ignore.
        if kwargs.get('ignore_existing_parent_field', False):
            pass
        else:
            raise FieldError("'{}' is already an existing model field.".format(parent_field_name))
    else:
        django_models.ForeignKey(
            'self',
            related_name='children',
            null=True,
            blank=True,
        ).contribute_to_class(model_class, parent_field_name)
