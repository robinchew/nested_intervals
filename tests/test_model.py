from django.core.exceptions import FieldError
from django.contrib.auth.models import Group
from django.db import models
from django.test import TestCase

import nested_intervals
from nested_intervals.matrix import Matrix
from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.tests.models import ExampleModel


def create_test_tree():
    root = ExampleModel()
    child_1 = ExampleModel()
    child_1.save_as_child_of(root)
    child_1_1 = ExampleModel()
    child_1_1.save_as_child_of(child_1)
    child_1_2 = ExampleModel()
    child_1_2.save_as_child_of(child_1)

    child_2 = ExampleModel()
    child_2.save_as_child_of(root)
    child_2_1 = ExampleModel()
    child_2_1.save_as_child_of(child_2)
    child_2_1_1 = ExampleModel()
    child_2_1_1.save_as_child_of(child_2_1)
    child_2_2 = ExampleModel()
    child_2_2.save_as_child_of(child_2)

    child_3 = ExampleModel()
    child_3.save_as_child_of(root)
    child_3_1 = ExampleModel()
    child_3_1.save_as_child_of(child_3)


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
        self.assertEqual(root.get_abs_matrix(), Matrix(1, 1, 1, 0))

        child1 = ExampleModel()
        child1.save_as_child_of(root)

        root, child1  = ExampleModel.objects.order_by('pk')
        self.assertEqual(child1.get_abs_matrix(), Matrix(1, 1, 2, 1))

        child2 = ExampleModel()
        child2.save_as_child_of(root)

        root, child1, child2 = ExampleModel.objects.order_by('pk')
        self.assertEqual(child2.get_abs_matrix(), Matrix(2, 1, 3, 1))

    def test_ancestors(self):
        create_test_tree()

        child_2_1_1 = ExampleModel.objects.get(
            **ExampleModel.build_nested_intervals_query_kwargs(4, 3, 7, 5))

        self.assertEqual(
            list(child_2_1_1.get_ancestors().order_by('pk')),
            [
                ExampleModel.objects.get(**ExampleModel.build_nested_intervals_query_kwargs(a11, a12, a21, a22))
                for a11, a12, a21, a22 in (
                    (2, 1, 3 ,1),
                    (3, 2, 5 ,3),
                )
            ])
