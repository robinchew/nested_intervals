from django.db import models
from django.db.models import Q
from django.db.models.base import ModelBase
from django.utils import six

from nested_intervals.managers import NestedIntervalsManager, NestedIntervalsQuerySet
from nested_intervals.matrix import Matrix, get_child_matrix, get_ancestors_matrix, get_root_matrix
from nested_intervals.matrix import INVISIBLE_ROOT_MATRIX
from nested_intervals.queryset import children_of
from nested_intervals.queryset import children_of_matrix


class NestedIntervalsModelMixin(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def build_nested_intervals_query_kwargs(cls, a11, a12, a21, a22):
        name11, name12, name21, name22 = cls._nested_intervals_field_names
        return {
            name11: abs(a11),
            name12: abs(a12),
            name21: abs(a21),
            name22: abs(a22),
        }

    def has_matrix(self):
        return any(
            getattr(self, field_name)
            for field_name in self._nested_intervals_field_names)

    def get_matrix(self):
        return Matrix(*(
            getattr(self, field_name) * (1 if (i % 2 == 0) else -1)
            for i, field_name in enumerate(self._nested_intervals_field_names)))

    def get_abs_matrix(self):
        return Matrix(*tuple(abs(num) for num in self.get_matrix()))

    def get_root(self):
        return self.__class__.objects.get(
            **self.__class__.build_nested_intervals_query_kwargs(
                *get_root_matrix(self.get_matrix())))

    def get_parent(self):
        name11, name12, name21, name22 = self._nested_intervals_field_names
        return self.__class__.objects.get(**{
            name11: getattr(self, name12),
            name21: getattr(self, name22)
        })

    def get_ancestors_query(self):
        return reduce(
            lambda a, b: a | Q(**self.__class__.build_nested_intervals_query_kwargs(*b)),
            get_ancestors_matrix(self.get_matrix()),
            Q())

    def get_ancestors(self):
        query = self.get_ancestors_query()
        if query:
            return self.__class__.objects.filter(query)
        return self.__class__.objects.none()

    def get_children(self):
        return children_of(self)

    def get_descendants(self):
        name11, name12, name21, name22 = self._nested_intervals_field_names
        a11, a12, a21, a22 = self.get_abs_matrix()

        s1 = a11 - a12 # 's' stands for sibling
        s2 = a21 - a22

        return self.__class__.objects.extra(
            where=[
                "({} * %s) >= (%s * {})".format(name11, name21),
                "({} * %s) <= (%s * {})".format(name12, name22)
            ],
            params=[s2, s1, a21, a11])

    def set_as_child_of(self, parent):
        """
        TODO
        1. This behaves wrongly when used on new Home instance that
           does not have any primary key set yet.
        2. This should also the change the matrix of the descendents
           of this instance.
        """
        num_children = children_of(parent).count()
        field_names = self._nested_intervals_field_names
        child_matrix = get_child_matrix(parent.get_matrix(), num_children+1)

        for field_name, num in zip(field_names, child_matrix):
            setattr(self, field_name, abs(num))

    def set_matrix(self, matrix):
        for field_name, num in zip(self._nested_intervals_field_names, matrix):
            setattr(self, field_name, abs(num))

    def save_as_child_of(self, parent, *args, **kwargs):
        self.set_as_child_of(parent)
        self.save(*args, **kwargs)
        return self

    def set_as_root(self):
        num_children = children_of_matrix(self.__class__.objects, INVISIBLE_ROOT_MATRIX).count()

        field_names = self._nested_intervals_field_names
        child_matrix = get_child_matrix(INVISIBLE_ROOT_MATRIX, num_children+1)

        for field_name, num in zip(field_names, child_matrix):
            setattr(self, field_name, abs(num))

    def save_as_root(self, *args, **kwargs):
        self.set_as_root()
        self.save(*args, **kwargs)
        return self
