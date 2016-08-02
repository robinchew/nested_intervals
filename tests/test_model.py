from django.core.exceptions import FieldError
from django.contrib.auth.models import Group
from django.db import models
from django.test import TestCase

import nested_intervals
from nested_intervals.matrix import Matrix
from nested_intervals.matrix import get_child_matrix
from nested_intervals.models import NestedIntervalsModelMixin
from nested_intervals.models import create
from nested_intervals.models import update
from nested_intervals.tests.models import ExampleModel
from nested_intervals.queryset import last_child_of


class Tree(dict):
    def __init__(self, d):
        self.d = d
        super(Tree, self).__init__(d)

    def __getitem__(self, key):
        return ExampleModel.objects.get(pk=self.d[key].pk)

    def items(self):
        return (self[k] for k in super(Tree, self))

    def formatted(self):
        return {
            (self[k].pk, self[k], k)
            for k in self
        }


def create_test_tree():
    root = ExampleModel()
    root.save_as_root() # 1 1 2 1
    child_1 = ExampleModel() # 1 1 3 2
    child_1.save_as_child_of(root)
    child_1_1 = ExampleModel() # 1 1 4 3
    child_1_1.save_as_child_of(child_1)
    child_1_2 = ExampleModel() # 2 1 7 3
    child_1_2.save_as_child_of(child_1)

    child_2 = ExampleModel() # 2 1 5 2
    child_2.save_as_child_of(root)
    child_2_1 = ExampleModel() # 3 2 8 5
    child_2_1.save_as_child_of(child_2)
    child_2_1_1 = ExampleModel() # 4 3 11 8
    child_2_1_1.save_as_child_of(child_2_1)
    child_2_2 = ExampleModel() # 5 2 13 5
    child_2_2.save_as_child_of(child_2)

    child_3 = ExampleModel() # 3 1 7 2
    child_3.save_as_child_of(root)
    child_3_1 = ExampleModel() # 5 3 12 7
    child_3_1.save_as_child_of(child_3)

    return Tree({
        '0': root,
        '1': child_1,
        '1.1': child_1_1,
        '1.2': child_1_2,
        '2': child_2,
        '2.1': child_2_1,
        '2.1.1': child_2_1_1,
        '2.2': child_2_2,
        '3': child_3,
        '3.1': child_3_1,
    })


class FakeModel(object):
    pass


class RootTest(TestCase):
    def test_save_two_roots(self):
        self.assertEqual(ExampleModel.objects.count(), 0)

        create(ExampleModel, [{'name': 'example1'}])

        model = ExampleModel.objects.all().get()

        self.assertEqual(model.lnumerator, 1)
        self.assertEqual(model.rnumerator, 1)
        self.assertEqual(model.ldenominator, 2)
        self.assertEqual(model.rdenominator, 1)

        create(ExampleModel, [{'name': 'example2'}])

        model1, model2 = ExampleModel.objects.order_by('pk')

        self.assertEqual(model2.lnumerator, 2)
        self.assertEqual(model2.rnumerator, 1)
        self.assertEqual(model2.ldenominator, 3)
        self.assertEqual(model2.rdenominator, 1)

    def test_root(self):
        tree = create_test_tree()

        self.assertEqual(
            ExampleModel.objects.get(**ExampleModel.build_nested_intervals_query_kwargs(2, 1, 5, 2)).get_root(),
            tree['0'])

    def test_save_root_after_deleting_old_root(self):
        create(ExampleModel, [{'name': 'example {}'.format(i+1)} for i in xrange(3)])
        root1, root2, root3 = ExampleModel.objects.order_by('pk')

        self.assertEqual(root1.get_matrix(), Matrix(1, -1, 2, -1))
        self.assertEqual(root2.get_matrix(), Matrix(2, -1, 3, -1))
        self.assertEqual(root3.get_matrix(), Matrix(3, -1, 4, -1))

        root2.delete()

        create(ExampleModel, [{'name': 'example 4'}])
        root1, root3, root4 = ExampleModel.objects.order_by('pk')
        self.assertEqual(root1.get_matrix(), Matrix(1, -1, 2, -1))
        self.assertEqual(root3.get_matrix(), Matrix(3, -1, 4, -1))
        self.assertEqual(root4.get_matrix(), Matrix(4, -1, 5, -1))


class TestModel(TestCase):
    def test_invalid_model(self):
        with self.assertRaises(FieldError) as context:
            class InvalidExampleModel(NestedIntervalsModelMixin, FakeModel):
                conflict = models.CharField()

            nested_intervals.register_fields(InvalidExampleModel, 'a11', 'conflict', 'a21', 'a22', 'parent')

        self.assertEqual(
            context.exception.message,
            "'conflict' is already an existing model field.")

    def test_create(self):
        self.assertEqual(ExampleModel.objects.count(), 0)
        create(ExampleModel, [
            {'name': 'example1',},
            {'name': 'example2',},
        ])
        self.assertEqual(
            [e.name for e in ExampleModel.objects.order_by('pk')],
            ['example1', 'example2'],
        )

    def test_root_save(self):
        root = create(ExampleModel, [{'name': 'example 1'}])
        root = ExampleModel.objects.all().get()
        self.assertEqual(root.get_matrix(), Matrix(1, -1, 2, -1))


class ChildTest(TestCase):
    def test_save_children(self):
        root = create(ExampleModel, [{'name': 'Root'}])
        root = ExampleModel.objects.all().get()

        self.assertEqual(root.get_abs_matrix(), Matrix(1, 1, 2, 1))
        self.assertEqual(root.parent, None)

        create(ExampleModel, [{'name': 'Child 1', 'parent': root.pk}])
        root, child1  = ExampleModel.objects.order_by('pk')

        self.assertEqual(child1.parent, root)
        self.assertEqual(child1.get_abs_matrix(), Matrix(1, 1, 3, 2))

        create(ExampleModel, [{'name': 'Child 2' ,'parent': root.pk}])

        root, child1, child2 = ExampleModel.objects.order_by('pk')
        self.assertEqual(child2.get_abs_matrix(), Matrix(2, 1, 5, 2))

    def test_ancestors(self):
        tree = create_test_tree()

        child_2_1_1 = ExampleModel.objects.get(
            **ExampleModel.build_nested_intervals_query_kwargs(4, 3, 11, 8))

        self.assertEqual(
            list(child_2_1_1.get_ancestors().order_by('pk')),
            [
                ExampleModel.objects.get(**ExampleModel.build_nested_intervals_query_kwargs(a11, a12, a21, a22))
                for a11, a12, a21, a22 in (
                    (1, 1, 2 ,1),
                    (2, 1, 5 ,2),
                    (3, 2, 8 ,5),
                )
            ])

        # Test no ancestor matches
        self.assertEqual(tree['0'].get_ancestors().count(), 0)

    def test_descendants(self):
        tree = create_test_tree()
        self.assertEqual(
            list(tree['2'].get_descendants().order_by('pk')),
            [tree[i] for i in ('2.1', '2.1.1', '2.2')])

        self.assertEqual(
            [node.parent for node in tree['2'].get_descendants().order_by('pk')],
            [tree[i] for i in ('2', '2.1', '2')])

    def test_move_child_to_new_parent_along_with_descendants(self):
        tree = create_test_tree()

        self.assertEqual(tree['2'].get_parent(), tree['0'])
        self.assertEqual(
            list(tree['2'].get_descendants().order_by('pk')),
            [tree[i] for i in ('2.1', '2.1.1', '2.2')]
        )

        # Make 2 child of 3

        for child in tree['2'].set_as_child_of(tree['3']):
            child.save()

        self.assertEqual(tree['2'].get_parent(), tree['3'])
        self.assertEqual(
            [i.pk for i in tree['2'].get_descendants().order_by('pk')],
            [tree[i].pk for i in ('2.1', '2.1.1', '2.2')]
        )
        self.assertEqual(tree['2'].parent, tree['3'])
        self.assertEqual(
            [i.parent for i in tree['2'].get_descendants().order_by('pk')],
            [tree[i] for i in ('2', '2.1', '2')]
        )

        self.assertEqual(
            [i.pk for i in tree['3'].get_descendants().order_by('pk')],
            [tree[i].pk for i in ('2', '2.1', '2.1.1', '2.2', '3.1')]
        )
        self.assertEqual(tree['2'].get_matrix(), get_child_matrix(tree['3'].get_matrix(), 2))
        self.assertEqual(tree['2'].get_matrix(), Matrix(8, -3, 19, -7))
        self.assertEqual(tree['2.1'].get_matrix(), Matrix(13, -8, 31, -19))
        self.assertEqual(tree['2.1.1'].get_matrix(), Matrix(18, -13, 43, -31))
        self.assertEqual(tree['2.2'].get_matrix(), Matrix(21, -8, 50, -19))

        # Make 2.1 child of 1.1

        tree['2.1'].save_as_child_of(tree['1.1'])

        self.assertEqual(
            [i.pk for i in tree['3'].get_descendants().order_by('pk')],
            [tree[i].pk for i in ('2', '2.2', '3.1')]
        )

        self.assertEqual(
            [i.pk for i in tree['1.1'].get_descendants().order_by('pk')],
            [tree[i].pk for i in ('2.1', '2.1.1')]
        )
        self.assertEqual(tree['2.1'].parent, tree['1.1'])
        self.assertEqual(
            [i.parent for i in tree['1.1'].get_descendants().order_by('pk')],
            [tree[i] for i in ('1.1', '2.1')]
        )

        self.assertEqual(
            tree['2.1'].get_matrix(),
            get_child_matrix(tree['1.1'].get_matrix(), 1)
        )
        self.assertEqual(
            tree['2.1.1'].get_matrix(),
            get_child_matrix(tree['2.1'].get_matrix(), 1)
        )
        self.assertEqual(
            tree['2.1.1'].get_matrix(),
            Matrix(1, -1, 6, -5)
        )

        # 2.2 remains unchanged
        self.assertEqual(tree['2.2'].get_matrix(), Matrix(21, -8, 50, -19))

    def test_save_child_repeatedly(self):
        """
        Saving the same child to the same parent will
        make the child younger and younger.
        """
        create(ExampleModel, [{'name': 'Root'}])
        root = ExampleModel.objects.all().get()

        create(ExampleModel, [{'name': 'Child 1', 'parent': root.pk}])
        root, child1 = ExampleModel.objects.all().order_by('pk')

        self.assertEqual(child1.get_abs_matrix(), Matrix(1, 1, 3, 2))

        update(ExampleModel, ('id', child1.pk), {'parent': root.pk})

        root, child1 = ExampleModel.objects.all().order_by('pk')
        self.assertEqual(child1.get_abs_matrix(), Matrix(2, 1, 5, 2))

    def test_set_child_after_deleting_sibling(self):
        create(ExampleModel, [{'name': 'Root'}]) # 1 1 2 1
        root = ExampleModel.objects.all().get()

        create(ExampleModel, [{'name': 'Child 1', 'parent': root.pk}]) # 1 1 3 2
        root, child1 = ExampleModel.objects.order_by('pk')

        create(ExampleModel, [{'name': 'Child 2', 'parent': root.pk}]) # 2 1 5 2
        root, child1, child2 = ExampleModel.objects.order_by('pk')

        create(ExampleModel, [{'name': 'Child 3', 'parent': root.pk}]) # 3 1 7 2
        root, child1, child2, child3 = ExampleModel.objects.order_by('pk')

        self.assertEqual(root.get_abs_matrix(), Matrix(1, 1, 2, 1))
        self.assertEqual(child1.get_abs_matrix(), Matrix(1, 1, 3, 2))
        self.assertEqual(child2.get_abs_matrix(), Matrix(2, 1, 5, 2))
        self.assertEqual(child3.get_abs_matrix(), Matrix(3, 1, 7, 2))

        child2.delete()

        self.assertEqual(last_child_of(root), child3)

        create(ExampleModel, [{'name': 'Child 4', 'parent': root.pk}]) # 4 1 9 2

        root, child1, child3, child4 = ExampleModel.objects.order_by('pk')
        self.assertEqual(child3.name, 'Child 3')
        self.assertEqual(child4.get_abs_matrix(), Matrix(4, 1, 9, 2))
