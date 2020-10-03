# third party
from lark import Tree, Token

# local
import py_csl_validator.expressions.expression_classes as ec
from .csl_visitor_1_1 import CslVisitor1_1


class CslVisitor1_2(CslVisitor1_1):

    def uri_decode_expr(self, stack):
        encoding = None
        string_provider = stack.pop()

        if stack:
            encoding, string_provider = string_provider, stack.pop()

        return ec.UriDecodeExpr(string_provider, encoding)




