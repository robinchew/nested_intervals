from django.core.exceptions import FieldError
from django.db import models
from django.db.models.base import ModelBase
from django.utils import six

from nested_intervals.managers import NestedIntervalsManager, NestedIntervalsQuerySet
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


class NestedIntervalsModelMixin(six.with_metaclass(NestedIntervalsModelBase, models.Model)):

    objects = models.Manager()
    nested_intervals = NestedIntervalsQuerySet.as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        assert len(self.nested_intervals_field_names) == 4, "Set 4 field names in in 'nested_intervals_field_names' attribute in your model."
        super(NestedIntervalsModelMixin, self).__init__(*args, **kwargs)

    def has_matrix(self):
        return any(
            getattr(self, field_name)
            for field_name in self.nested_intervals_field_names)

    def get_matrix(self):
        return Matrix(*(
            getattr(self, field_name) * (1 if (i % 2 == 0) else -1)
            for i, field_name in enumerate(self.nested_intervals_field_names)))

    def get_abs_matrix(self):
        return tuple(abs(num) for num in self.get_matrix())

    def set_as_child_of(self, parent):
        num_children = self.__class__.nested_intervals.children_of(parent).count()
        field_names = self.nested_intervals_field_names
        child_matrix = get_child_matrix(parent.get_matrix(), num_children)

        for field_name, num in zip(field_names, child_matrix):
            setattr(self, field_name, abs(num))

    def save_as_child_of(self, parent, *args, **kwargs):
        self.set_as_child_of(parent)
        self.save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.has_matrix():
            for field_name, num in zip(self.nested_intervals_field_names, NESTED_INTERVALS_ROOT):
                setattr(self, field_name, abs(num))

        super(NestedIntervalsModelMixin, self).save(*args, **kwargs)
