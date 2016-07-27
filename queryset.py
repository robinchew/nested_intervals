from django.db import models
from django.db.models import F

from nested_intervals.matrix import get_child_matrix
from nested_intervals.exceptions import NoChildrenError
from nested_intervals.validation import validate_node

import functools
import operator

def children_of_matrix(queryset, matrix):
    name11, name12, name21, name22 = queryset.model._nested_intervals_field_names
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
        }).order_by((F(name11) * F(name12)).desc())[0]
    except IndexError:
        raise NoChildrenError()

def last_child_of(parent):
    validate_node(parent)
    name11, name12, name21, name22, parent_name = parent._nested_intervals_field_names
    try:
        return children_of(parent).order_by((F(name11) * F(name12)).desc())[0]
    except IndexError:
        raise NoChildrenError()

def reroot_matrix(node, root_matrix):
    validate_node(node)
    children = node.get_children()
    node.set_matrix(root_matrix)

    descendants = functools.reduce(
        operator.add,
        (
            reroot_matrix(
                child,
                get_child_matrix(root_matrix, i+1)
            )
            for i, child in enumerate(children)
        ),
        (),
    )
    return (node,) + tuple(children) + descendants

class NestedIntervalsQuerySet(models.QuerySet):
    def children_of(self, parent):
        return children_of(self, parent)
