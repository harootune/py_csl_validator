# local
from .expression_classes_1_1 import Expressions1_1


# Schema
class Expressions1_2(Expressions1_1):

    class UriDecodeExpr(DataExpr):

        def __init__(self, string_provider, encoding):
            self.string_provider = string_provider
            self.encoding = encoding

        def evaluate(self, row, context):
            pass














