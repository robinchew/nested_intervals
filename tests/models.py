from django.db import models

import nested_intervals
from nested_intervals import register_fields
from nested_intervals.models import NestedIntervalsModelMixin


class ExampleModel(NestedIntervalsModelMixin, models.Model):
    name = models.CharField(max_length=10)

    def __unicode__(self):
        return u'{} {} {} {}'.format(
            self.lnumerator,
            self.rnumerator,
            self.ldenominator,
            self.rdenominator)

nested_intervals.register_fields(ExampleModel, 'lnumerator','rnumerator', 'ldenominator', 'rdenominator', 'parent')


class ExampleModelWithoutNestedIntervals(models.Model):
    name = models.CharField(max_length=10)
