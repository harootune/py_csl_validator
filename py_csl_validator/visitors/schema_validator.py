# local
from .csl_visitor import CslVisitor


class CslRuleset(CslVisitor):

    def __init__(self, tree):
        super().__init__()

        self.visit(tree)

        self.schema = self.stack.pop()

