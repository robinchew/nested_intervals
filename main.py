from matrix import Matrix as M

print '1st child of root:', M(1, -1, 1 ,0) * M(1+1, -1, 1, 0) 

def make_child_of(matrix, nth):
    return matrix * M(nth+1, -1, 1, 0)

root = M(1, -1, 1, 0)

first_child = make_child_of(root, 1) 
second_child = make_child_of(root, 2) 

print '2nd child of root:', second_child

print '1st grand child', make_child_of(first_child, 1)
print '2nd grand child', make_child_of(first_child, 2)
print '3rd grand child', make_child_of(first_child, 3)

print
print '1st grand child of child 2', make_child_of(second_child, 1)
