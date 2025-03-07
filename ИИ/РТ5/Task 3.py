class Tree:
    def __init__(self, data):
        self.left = None
        self.right = None
        self.data = data

    def PrintTree(self):
        if self.left:
            self.left.PrintTree()
        print(self.data)
        if self.right:
            self.right.PrintTree()

    def AddElement(self, Element):
        if self.data:
            if Element < self.data:
                if self.left is None:
                    self.left = Tree(Element)
                else:
                    self.left.AddElement(Element)
            elif Element >= self.data:
                if self.right is None:
                    self.right = Tree(Element)
                else:
                    self.right.AddElement(Element)
        else:
            self.data = Element