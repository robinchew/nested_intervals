from django.db import models
from django.db.models import F

from nested_intervals.exceptions import InvalidNodeError
from nested_intervals.matrix import get_child_matrix
from nested_intervals.matrix import INVISIBLE_ROOT_MATRIX
from nested_intervals.matrix import Matrix
from nested_intervals.exceptions import NoChildrenError
from nested_intervals.validation import validate_node

import functools
import operator

######################
# INSTANCE FUNCTIONS #
######################

def get_matrix(instance):
    return Matrix(*(
        getattr(instance, field_name) * (1 if (i % 2 == 0) else -1)
        for i, field_name in enumerate(instance._nested_intervals_field_names[0:-1]))
    )

def get_nth(instance):
    n11, n12, n21, n22, parent_name = instance._nested_intervals_field_names
    return int(getattr(instance, n11) / getattr(instance, n12))

def set_matrix(instance, matrix):
    for field_name, num in zip(instance._nested_intervals_field_names, matrix):
        setattr(instance, field_name, abs(num))

def set_parent(instance, parent):
    parent_name = instance._nested_intervals_field_names[-1]
    setattr(instance, parent_name, parent)

def set_as_child_of(instance, parent):
    if parent:
        parent_matrix = parent.get_matrix()
    else:
        parent_matrix = INVISIBLE_ROOT_MATRIX
    child_matrix = get_child_matrix(
        parent_matrix,
        last_child_nth_of(type(instance).objects, parent_matrix) + 1)

    try:
        validate_node(instance)
    except InvalidNodeError:
        # A new model instance is being created,
        # so a setting the matrix is enough.
        set_matrix(instance, child_matrix)
        set_parent(instance, parent)
        return (instance,)

    # instance is an existing model instance which may have
    # descendants, so the instance and its descendants'
    # matrices must be updated, using the reroot function.
    return reroot(instance, parent, child_matrix)

def save_as_child_of(instance, parent, *args, **kwargs):
    nodes = set_as_child_of(instance, parent)
    for node in nodes:
        node.save(*args, **kwargs)
    return nodes

def set_as_root(instance):
    return set_as_child_of(instance, None)

def save_as_root(instance, *args, **kwargs):
    instance.set_as_root()
    instance.save(*args, **kwargs)
    return instance

######################
# QUERYSET FUNCTIONS #
######################

def children_of_matrix(queryset, matrix):
    name11, name12, name21, name22 = queryset.model._nested_intervals_field_names[0:4]
    parent_value11, parent_value12, parent_value21, parent_value22 = matrix

    return queryset.filter(**{
        name12: parent_value11,
        name22: parent_value21
    })

def children_of(parent, queryset=None):
    validate_node(parent)
    if queryset is None:
        queryset = parent.__class__.objects

    name11, name12, name21, name22, parent_name = parent._nested_intervals_field_names
    parent_value11, parent_value12, parent_value21, parent_value22 = parent.get_abs_matrix()

    return queryset.filter(**{
        name12: parent_value11,
        name22: parent_value21
    })

def last_child_of_matrix(queryset, parent_matrix):
    name11, name12, name21, name22, parent_name = queryset.model._nested_intervals_field_names
    v11, v12, v21, v22 = (abs(v) for v in parent_matrix)

    try:
        return queryset.filter(**{
            name12: v11,
            name22: v21
        }).order_by((F(name11) / F(name12)).desc())[0]
    except IndexError:
        raise NoChildrenError()

def last_child_of(parent):
    validate_node(parent)
    name11, name12, name21, name22, parent_name = parent._nested_intervals_field_names
    try:
        return children_of(parent).order_by((F(name11) / F(name12)).desc())[0]
    except IndexError:
        raise NoChildrenError()

def last_child_nth_of(queryset, parent_matrix):
    try:
        last_child = last_child_of_matrix(queryset, parent_matrix)
        return get_nth(last_child)
    except NoChildrenError:
        return 0

def reroot(node, parent, child_matrix):
    validate_node(node)
    validate_node(parent)
    parent_matrix = parent.get_matrix()
    children = node.get_children()

    node.set_matrix(child_matrix)
    node.set_parent(parent)

    descendants = functools.reduce(
        operator.add,
        (
            reroot(
                child,
                node,
                get_child_matrix(child_matrix, i+1))
            for i, child in enumerate(children)
        ),
        (),
    )
    return (node,) + tuple(children) + descendants

class NestedIntervalsQuerySet(models.QuerySet):
    def children_of(self, parent):
        return children_of(self, parent)
