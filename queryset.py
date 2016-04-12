from django.db import models

def children_of(parent, queryset=None):
    if queryset is None:
        queryset = parent.__class__.objects

    name11, name12, name21, name22 = parent._nested_intervals_field_names
    parent_value11, parent_value12, parent_value21, parent_value22 = parent.get_abs_matrix()

    return queryset.filter(**{
        name12: parent_value11,
        name22: parent_value21
    })

class NestedIntervalsQuerySet(models.QuerySet):
    def children_of(self, parent):
        return children_of(self, parent)
