from django.core.exceptions import FieldError
from django.db import models
from django.db.models.base import ModelBase
from django.utils import six

from nested_intervals.managers import NestedIntervalsManager, NestedIntervalsQuerySet
from nested_intervals.matrix import Matrix, get_child_matrix


class NestedIntervalsModelMixin(models.Model):
    class Meta:
        abstract = True

    def has_matrix(self):
        return any(
            getattr(self, field_name)
            for field_name in self._nested_intervals_field_names)

    def get_matrix(self):
        return Matrix(*(
            getattr(self, field_name) * (1 if (i % 2 == 0) else -1)
            for i, field_name in enumerate(self._nested_intervals_field_names)))

    def get_abs_matrix(self):
        return tuple(abs(num) for num in self.get_matrix())

    def get_root(self):
        # The root is the only node with
        # no row value in the database.
        return self.__class__(**{
            field_name: abs(num)
            for field_name, num in zip(self._nested_intervals_field_names, ROOT_MATRIX)})

    def set_as_child_of(self, parent):
        assert type(getattr(self.__class__, 'nested_intervals')) is NestedIntervalsManager
        num_children = self.__class__.nested_intervals.children_of(parent).count()
        field_names = self._nested_intervals_field_names
        child_matrix = get_child_matrix(parent.get_matrix(), num_children+1)

        for field_name, num in zip(field_names, child_matrix):
            setattr(self, field_name, abs(num))

    def save_as_child_of(self, parent, *args, **kwargs):
        self.set_as_child_of(parent)
        self.save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.has_matrix():
            self.set_as_child_of(self.get_root())

        super(NestedIntervalsModelMixin, self).save(*args, **kwargs)
