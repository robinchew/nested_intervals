from django.db import models
from nested_intervals.models import NestedIntervalsModelMixin


class ExampleModel(NestedIntervalsModelMixin, models.Model):
    nested_intervals_field_names = ('lnumerator', 'ldenominator', 'rnumerator', 'rdenominator')


class InvalidExampleModel(NestedIntervalsModelMixin, models.Model):
    pass
