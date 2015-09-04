from django.db import models
from nested_intervals.queryset import NestedIntervalsQuerySet

NestedIntervalsManager = models.Manager.from_queryset(NestedIntervalsQuerySet)
