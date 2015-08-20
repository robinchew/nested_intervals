from django.core.exceptions import FieldError
from django.db import models
from django.db.models.base import ModelBase
from django.utils import six

from nested_intervals.matrix import Matrix, get_child_matrix

NESTED_INTERVALS_ROOT = Matrix(1, -1, 1, 0)


class NestedIntervalsModelBase(ModelBase):
    def __new__(metaclass, class_name, bases, attrs):
        try:
            name1, name2, name3, name4 = attrs.get('nested_intervals_field_names')

            for field_name in (name1, name2, name3, name4):
                if field_name in attrs:
                    raise FieldError("'{}' is already an existing model field.".format(field_name))

            attrs[name1] = models.PositiveIntegerField()
            attrs[name2] = models.PositiveIntegerField()
            attrs[name3] = models.PositiveIntegerField()
            attrs[name4] = models.PositiveIntegerField()

        except TypeError:
            pass

        return super(NestedIntervalsModelBase, metaclass).__new__(metaclass, class_name, bases, attrs)


class NestedIntervalsModelMixin(six.with_metaclass(NestedIntervalsModelBase, object)):
    def __init__(self, *args, **kwargs):
        assert len(self.nested_intervals_field_names) == 4, "Set 4 field names in in 'nested_intervals_field_names' attribute in your model."
        super(NestedIntervalsModelMixin, self).__init__(*args, **kwargs)

    def save_as_child_of(self, node):
        num_children = self.__class__.objects.filter(node).count()
        return get_child_matrix(node, self.__class__.objects.count())

    def save(self, *args, **kwargs):
        for field_name, value in zip(self.nested_intervals_field_names, NESTED_INTERVALS_ROOT):
            setattr(self, field_name, value)

        return super(NestedIntervalsModelMixin, self).save(*args, **kwargs)
