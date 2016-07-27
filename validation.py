def validate_node(node):
    assert node.pk, 'node must be an existing model instance'
    for name in node._nested_intervals_field_names:
        assert getattr(node, name) is not None, "'{}' does not have a value set for '{}'".format(node, name)
