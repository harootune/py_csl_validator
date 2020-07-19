# third party
from lark import Tree, Token


class CslVisitor:

    def __init__(self, tree):
        self.ruleset = self.visit(tree)

    def visit(self, node):
        if isinstance(node, Token):
            return node.value
        elif isinstance(node, Tree):
            stack = [self.visit(child) for child in node.children]
            stack = [element for element in stack if element is not None]
            return self._call_expression(node, stack)

    def _call_expression(self, node, stack):
        return getattr(self, node.data, self.__default__)(stack)

    def __default__(self, stack):
        if not stack:
            return None
        elif len(stack) == 1:
            return stack.pop()
        else:
            raise AttributeError('Complex stack passed to default')
