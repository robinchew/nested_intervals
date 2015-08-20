from django.db import models

class NestedIntervalsQuerySet(models.QuerySet):
    def children_of(self, parent):
        name11, name12, name21, name22 = parent.nested_intervals_field_names
        parent_value11, parent_value12, parent_value21, parent_value22 = parent.get_abs_matrix()

        return self.filter(**{
            name12: parent_value11,
            name22: parent_value21
        })


NestedIntervalsManager = models.Manager.from_queryset(NestedIntervalsQuerySet)
