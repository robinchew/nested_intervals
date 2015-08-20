from django.core.exceptions import FieldError
from django.db import models
from django.test import TestCase

from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.tests.models import ExampleModel, InvalidExampleModel


class FakeModel(object):
    pass


class TestModel(TestCase):
    def test_invalid_model(self):
        with self.assertRaises(AttributeError) as context:
            InvalidExampleModel()

        self.assertIn("object has no attribute 'nested_intervals_field_names'", context.exception.message)

    def test_invalid_model_2(self):
        with self.assertRaises(FieldError) as context:
            class InvalidExampleModel2(NestedIntervalsModelMixin, FakeModel):
                nested_intervals_field_names = ('a11', 'conflict', 'a21', 'a22')
                conflict = models.CharField()

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
        self.assertEqual(model.rnumerator, 2)
        self.assertEqual(model.rdenominator, 1)

        model = ExampleModel()
        model.save()

        model1, model2 = ExampleModel.objects.order_by('pk')

        self.assertEqual(model2.lnumerator, 2)
        self.assertEqual(model2.ldenominator, 1)
        self.assertEqual(model2.rnumerator, 3)
        self.assertEqual(model2.rdenominator, 1)

    def test_save_children(self):
        root = ExampleModel()
        root.save()

        root = ExampleModel.objects.get(pk=root.pk)
        self.assertEqual(root.get_abs_matrix(), (1, 1, 2, 1))

        child1 = ExampleModel()
        child1.save_as_child_of(root)

        child1 = ExampleModel.objects.get(pk=child1.pk)
        self.assertEqual(child1.get_abs_matrix(), (1, 1, 3, 2))
