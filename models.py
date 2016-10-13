from django.db import connection
from django.db import models
from django.db import transaction
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

from sql import Literal
from sql import Null
from sql import Table

from functools import reduce
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

    def get_family_line(self):
        """
        This includes self, ancestors, and descendants.
        This EXCLUDES siblings and cousins.
        """
        return self.get_ancestors() | self.get_descendants() | self.__class__.objects.filter(pk=self.pk)

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

def validate_multi_column_values(d_list, allowed_columns):
    for d in d_list:
        for column, value in d.iteritems():
            assert column in allowed_columns, "'{}' is not set as allowed".format(column)

    d1, d2 = tee(d_list)
    next(d2, None)

    for a, b in izip(d1, d2):
        remaining_keys = set(a.keys()).difference(b.keys())
        assert len(remaining_keys) == 0, 'All column values must have matching keys. These keys are mismatched: {}.'.format(', '.join(remaining_keys))

def clean_field_name(Model, name):
    if issubclass(type(Model._meta.get_field(name)), models.ForeignKey):
        return name+'_id'
    return name

def clean_nested_intervals_by_parent_id(Model, parent_id=None, i=0):
    if parent_id:
        parent = Model.objects.get(pk=parent_id)
        parent_matrix = parent.get_matrix()
    else:
        parent_matrix = INVISIBLE_ROOT_MATRIX

    child_matrix = get_child_matrix(
        parent_matrix,
        Model.last_child_nth_of(parent_matrix) + i + 1
    )

    return {
        clean_field_name(Model, name): value
        for name, value in izip(Model._nested_intervals_field_names[0:-1], imap(abs, child_matrix))
    }

def clean_nested_intervals(Model, d, i=0):
    if issubclass(Model, NestedIntervalsModelMixin):
        parent_name = Model._nested_intervals_field_names[-1]
        if parent_name in d:
            return clean_nested_intervals_by_parent_id(Model, d[parent_name], i)
    return {}

def clean_default(Model, d, i=0):
    return ChainMap(
        {
            clean_field_name(Model, name): value
            for name, value in d.iteritems()
        },
        clean_nested_intervals(Model, d, i)
    )

def create(Model, allowed_columns, multi_column_values):
    table = Table(Model._meta.db_table)
    validate_multi_column_values(multi_column_values, allowed_columns)

    for fields in [clean_default(Model, d, i) for i, d in enumerate(multi_column_values)]:
        instance = Model()
        for field, value in fields.iteritems():
            setattr(instance, field, value)
        instance.save()
    return instance.pk

@transaction.atomic
def update(Model, allowed_columns, pk_column_value, column_values):
    for column, value in column_values.iteritems():
        assert column in allowed_columns, "'{}' is not set as allowed".format(column)

    table = Table(Model._meta.db_table)

    cvalues1, cvalues2  = tee(clean_default(Model, column_values).iteritems())

    table_columns = [
        getattr(table, column)
        for column, value in cvalues1
    ]

    with connection.cursor() as cursor:
        def where_and(a, b):
            bkey, bvalue = b
            return a & (getattr(table, bkey) == bvalue)

        cursor.execute(*table.update(
            columns=table_columns,
            values=[value for column, value in cvalues2],
            where=reduce(
                where_and,
                pk_column_value.iteritems(),
                Literal(1) == Literal(1)) # Hacky way to generate filter using reduce with initial value
        ))
        assert cursor.rowcount == 1, 'Expect only 1 SQL Update. Got {} instead. pk_column_value={}'.format(cursor.rowcount, pk_column_value)

    # Updating a node's parent should result in
    # updating of the node's descendants.

    if issubclass(Model, NestedIntervalsModelMixin):
        parent_name = Model._nested_intervals_field_names[-1]
        if parent_name in column_values:
            children = Model.objects.filter(parent=pk_value).iterator()
            for child in children:
                update(Model, allowed_columns, (pk_key, child.pk), {
                    'parent': pk_value,
                })
