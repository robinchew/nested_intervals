from django.db import connection
from django.db import models
from django.db.models import Q
from django.db.models.base import ModelBase
from django.utils import six

from nested_intervals.exceptions import NoChildrenError
from nested_intervals.exceptions import InvalidNodeError
from nested_intervals.managers import NestedIntervalsManager, NestedIntervalsQuerySet
from nested_intervals.matrix import Matrix, get_child_matrix, get_ancestors_matrix, get_root_matrix
from nested_intervals.matrix import INVISIBLE_ROOT_MATRIX

from nested_intervals.queryset import children_of
from nested_intervals.queryset import children_of_matrix
from nested_intervals.queryset import last_child_of
from nested_intervals.queryset import last_child_of_matrix
from nested_intervals.queryset import reroot

from nested_intervals.validation import validate_node

from sql import Table

from itertools import imap, izip, tee

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap


class NestedIntervalsModelMixin(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def build_nested_intervals_query_kwargs(cls, a11, a12, a21, a22):
        name11, name12, name21, name22, parent_name = cls._nested_intervals_field_names
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
            for i, field_name in enumerate(self._nested_intervals_field_names[0:-1]))
        )

    def get_abs_matrix(self):
        return Matrix(*tuple(abs(num) for num in self.get_matrix()))

    def get_root(self):
        return self.__class__.objects.get(
            **self.__class__.build_nested_intervals_query_kwargs(
                *get_root_matrix(self.get_matrix())))

    def get_parent(self):
        name11, name12, name21, name22, parent_name = self._nested_intervals_field_names
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
        name11, name12, name21, name22, parent_name = self._nested_intervals_field_names
        a11, a12, a21, a22 = self.get_abs_matrix()

        s1 = a11 - a12 # 's' stands for sibling
        s2 = a21 - a22

        return self.__class__.objects.extra(
            where=[
                "({} * %s) >= (%s * {})".format(name11, name21),
                "({} * %s) <= (%s * {})".format(name12, name22)
            ],
            params=[s2, s1, a21, a11])

    def get_nth(self):
        n11, n12, n21, n22, parent_name = self._nested_intervals_field_names
        return int(getattr(self, n11) / getattr(self, n12))

    def set_matrix(self, matrix):
        for field_name, num in zip(self._nested_intervals_field_names, matrix):
            setattr(self, field_name, abs(num))

    def set_parent(self, parent):
        parent_name = self._nested_intervals_field_names[-1]
        setattr(self, parent_name, parent)

    @classmethod
    def last_child_nth_of(cls, parent_matrix):
        try:
            last_child = last_child_of_matrix(cls.objects, parent_matrix)
            return last_child.get_nth()
        except NoChildrenError:
            return 0

    def set_as_child_of(self, parent):
        if parent:
            parent_matrix = parent.get_matrix()
        else:
            parent_matrix = INVISIBLE_ROOT_MATRIX
        child_matrix = get_child_matrix(
            parent_matrix,
            type(self).last_child_nth_of(parent_matrix) + 1
        )

        try:
            validate_node(self)
        except InvalidNodeError:
            # A new model instance is being created,
            # so a setting the matrix is enough.
            self.set_matrix(child_matrix)
            self.set_parent(parent)
            return (self,)

        # self is an existing model instance which may have
        # descendants, so the instance and its descendants'
        # matrices must be updated, using the reroot function.
        return reroot(self, parent, child_matrix)

    def set_as_root(self):
        return self.set_as_child_of(None)

    def save_as_child_of(self, parent, *args, **kwargs):
        nodes = self.set_as_child_of(parent)
        for node in nodes:
            node.save(*args, **kwargs)
        return nodes

    def save_as_root(self, *args, **kwargs):
        self.set_as_root()
        self.save(*args, **kwargs)
        return self

def validate_multi_column_values(d_list):
    d1, d2 = tee(d_list)
    next(d2, None)

    for a, b in izip(d1, d2):
        remaining_keys = set(a.keys()).difference(b.keys())
        if len(remaining_keys):
            raise Exception('All column values must have matching keys. These keys are mismatched: {}.'.format(', '.join(remaining_keys)))

def clean(Model, d):
    parent_name = Model._nested_intervals_field_names[-1]
    if parent_name in d:
        parent = Model.objects.get(**{parent_name: d[parent_name]})
        parent_matrix = parent.get_matrix()
    else:
        parent_matrix = INVISIBLE_ROOT_MATRIX

    child_matrix = get_child_matrix(
        parent_matrix,
        Model.last_child_nth_of(parent_matrix) + 1
    )

    return ChainMap(
        {
            name: value
            for name, value in izip(Model._nested_intervals_field_names[0:-1], imap(abs, child_matrix))
        },
        d
    )

def multi_clean(Model, l):
    return [clean(Model, d) for d in l]

def create(Model, multi_column_values):
    table = Table(Model._meta.db_table)
    validate_multi_column_values(multi_column_values)

    clean_multi_column_values = multi_clean(Model, multi_column_values)

    column_names = clean_multi_column_values[0].keys()

    table_columns = [
        getattr(table, key)
        for key in column_names
    ]

    cursor = connection.cursor()
    cursor.execute(*table.insert(
        columns=table_columns,
        values=[
            [
                column_values[column]
                for column in column_names
            ]
            for column_values in clean_multi_column_values
        ]
    ))

def update(Model, pk_column_value, column_values):
    assert len(pk_column_value) == 1
    pk_key, pk_value = pk_column_value
    table = Table(Model._meta.db_table)

    cvalues1, cvalues2  = tee(column_values)

    table.update(
        columns=[column for column, value in cvalues1],
        values=[value for column, value in cvalues2],
        where=getattr(table, pk_key) == pk_value
    )
