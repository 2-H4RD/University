class Tree:
    def __init__(self, kids, next=None):
        self.kids = self.val = kids
        self.next = next

t = Tree(Tree('a', Tree('b', Tree('d', 'e'))), Tree('c', Tree('f')))

print('main = ', t.kids.val)

print('left subtree = ', end='')
print(t.kids.next.val, end=', ')
print(t.kids.next.next.val, end=', ')
print(t.kids.next.next.next)

print('right subtree = ', end='')
print(t.next.kids, end=', ')
print(t.next.next.kids)