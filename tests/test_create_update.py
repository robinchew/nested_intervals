from django.test import TestCase

from nested_intervals.models import create
from nested_intervals.models import update
from nested_intervals.tests.models import ExampleModelWithoutNestedIntervals

try:
    pass
except ImportError:
    pass

def create_for_test(*names):
    create(ExampleModelWithoutNestedIntervals, ('name',), tuple(
        {'name': name}
        for name in names))


class ModelCreateUpdateTest(TestCase):
    def test_create(self):
        self.assertEqual(ExampleModelWithoutNestedIntervals.objects.count(), 0)
        create_for_test('First', 'Second')
        first, second = ExampleModelWithoutNestedIntervals.objects.order_by('pk')
        self.assertEqual([first.name, second.name], ['First', 'Second'])

    def test_update(self):
        self.test_create()
        first, second = ExampleModelWithoutNestedIntervals.objects.order_by('pk')

        update(ExampleModelWithoutNestedIntervals,
            ('name',),
            ('id', second.pk),
            {'name': 'Second2'},
        )

        first, second = ExampleModelWithoutNestedIntervals.objects.order_by('pk')
        self.assertEqual([first.name, second.name], ['First', 'Second2'])

    def test_update_one_only(self):
        """
        Update should affect one row only, or else rollback.
        """
        create_for_test('First', 'First')
        assert ExampleModelWithoutNestedIntervals.objects.count() == 2

        with self.assertRaises(AssertionError) as assertion:
            update(ExampleModelWithoutNestedIntervals,
                ('name',),
                ('name', 'First'),
                {'name': 'Second'},
            )

        assert 'Expect only 1' in assertion.exception.message
        assert 'Got 2' in assertion.exception.message

        # No changes happened
        assert ['First', 'First'] == [
            obj.name
            for obj in ExampleModelWithoutNestedIntervals.objects.iterator()
        ]
