from django.db import models

import nested_intervals
from nested_intervals import register_fields
from nested_intervals.models import NestedIntervalsModelMixin


class ExampleModel(NestedIntervalsModelMixin, models.Model):
    pass

nested_intervals.register_fields(ExampleModel, 'lnumerator', 'ldenominator', 'rnumerator', 'rdenominator')
