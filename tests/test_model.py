from django.core.exceptions import FieldError
from django.contrib.auth.models import Group
from django.db import models
from django.test import TestCase

import nested_intervals
from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.tests.models import ExampleModel


class FakeModel(object):
    pass


class TestModel(TestCase):
    def test_invalid_model(self):
        with self.assertRaises(FieldError) as context:
            class InvalidExampleModel(NestedIntervalsModelMixin, FakeModel):
                conflict = models.CharField()

            nested_intervals.register_fields(InvalidExampleModel, 'a11', 'conflict', 'a21', 'a22')

        self.assertEqual(
            context.exception.message,
            "'conflict' is already an existing model field.")

    def test_save_two_roots(self):
        self.assertEqual(ExampleModel.objects.count(), 0)

        model = ExampleModel()
        model.save()

        model = ExampleModel.objects.all().get()

        self.assertEqual(model.lnumerator, 1)
        self.assertEqual(model.ldenominator, 1)
        self.assertEqual(model.rnumerator, 1)
        self.assertEqual(model.rdenominator, 0)

        model = ExampleModel()
        model.save()

        model1, model2 = ExampleModel.objects.order_by('pk')

        self.assertEqual(model2.lnumerator, 1)
        self.assertEqual(model2.ldenominator, 1)
        self.assertEqual(model2.rnumerator, 1)
        self.assertEqual(model2.rdenominator, 0)

    def test_save_children(self):
        root = ExampleModel()
        root.save()

        root = ExampleModel.objects.all().get()
        self.assertEqual(root.get_abs_matrix(), (1, 1, 1, 0))

        child1 = ExampleModel()
        child1.save_as_child_of(root)

        root, child1  = ExampleModel.objects.order_by('pk')
        self.assertEqual(child1.get_abs_matrix(), (1, 1, 2, 1))

        child2 = ExampleModel()
        child2.save_as_child_of(root)

        root, child1, child2 = ExampleModel.objects.order_by('pk')
        self.assertEqual(child2.get_abs_matrix(), (2, 1, 3, 1))
