# third party
from lark import Tree, Token

# local
from py_csl_validator.expressions.expression_index import ExpressionIndex


class CslVisitor:
    index = ExpressionIndex.get_index()

    def __init__(self):
        self.stack = []

    def visit(self, tree):
        for child in tree.children:
            if isinstance(child, Token):
                self.stack.append(child.value)
            elif isinstance(child, Tree):
                self.visit(child)

        self.index.call_expression(self, tree)

