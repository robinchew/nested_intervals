from .exceptions import InvalidNodeError

def valid_assert(is_true, message):
    if not is_true:
        raise InvalidNodeError(message)

def validate_node(node):
    valid_assert(node.pk, "'node' must be an existing model instance")
    for name in node._nested_intervals_field_names:
        valid_assert(getattr(node, name) is not None, "'{}' does not have a value set for '{}'".format(node, name))
