from django.db import models
from django.db.models import F

from nested_intervals.exceptions import NoChildrenError

def children_of_matrix(queryset, matrix):
    name11, name12, name21, name22 = queryset.model._nested_intervals_field_names
    parent_value11, parent_value12, parent_value21, parent_value22 = matrix

    return queryset.filter(**{
        name12: parent_value11,
        name22: parent_value21
    })

def children_of(parent, queryset=None):
    if queryset is None:
        queryset = parent.__class__.objects

    name11, name12, name21, name22 = parent._nested_intervals_field_names
    parent_value11, parent_value12, parent_value21, parent_value22 = parent.get_abs_matrix()

    return queryset.filter(**{
        name12: parent_value11,
        name22: parent_value21
    })

def last_child_of(parent):
    name11, name12, name21, name22 = parent._nested_intervals_field_names
    try:
        return children_of(parent).order_by((F(name11) * F(name12)).desc())[0]
    except IndexError:
        raise NoChildrenError()

class NestedIntervalsQuerySet(models.QuerySet):
    def children_of(self, parent):
        return children_of(self, parent)
