class Schema:  # TODO: Should this be a ValidatingExpr?

    def __init__(self, body, prolog):
        self.body = body
        self.prolog = prolog


# Prolog #


class GlobalDirectives:

    def __init__(self, directives):
        self.directives = directives


class GlobalDirective:
    pass


class SeparatorDirective(GlobalDirective):

    def __init__(self, separator):
        self.separator = separator


class TotalColumnsDirective(GlobalDirective):

    def __init__(self, num_columns):
        self.num_columns = num_columns


# Body #


class ValidatingExpr:

    def validate(self, val):
        raise NotImplementedError


class Body(ValidatingExpr):

    def __init__(self, column_defs):
        self.column_defs = column_defs

    def validate(self, val):
        pass


class ColumnDefinition(ValidatingExpr):

    def __init__(self, col_name, col_rule):
        self.name = col_name
        self.rule = col_rule

    def validate(self, val):
        pass


class ColumnRule(ValidatingExpr):

    def __init__(self, col_vals, col_directives):
        self.col_vals = col_vals
        self.col_directives = col_directives

    def validate(self, val):
        pass


class ColumnValidationExpr(ValidatingExpr):  # essentially a wrapper which makes checks for comb/noncomb expr easier

    def __init__(self, expression):
        self.expression = expression

    def validate(self, val):
        pass


class ParenthesizedExpr(ValidatingExpr):

    def __init__(self, expressions):
        self.expressions = expressions

    def validate(self, val):
        pass


class SingleExpr(ValidatingExpr):

    def __init__(self, expression, col_ref):
        self.expression = expression
        self.col_Ref = col_ref

    def validate(self, val):
        pass


class IsExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val):
        pass


class AnyExpr(ValidatingExpr):

    def __init__(self, comparisons):
        self.comparisons = comparisons

    def validate(self, val):
        pass


class NotExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val):
        pass


class InExpr(ValidatingExpr):

    def __init__(self, comparison):
        self. comparison = comparison

    def validate(self, val):
        pass


class StartsWithExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val):
        pass


class EndsWithExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val):
        pass


class RegExpExpr(ValidatingExpr):

    def __init__(self, pattern):
        self.pattern = pattern

    def validate(self, val):
        pass


class RangeExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class LengthExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class EmptyExpr(ValidatingExpr):

    def validate(self, val):
        pass


class NotEmptyExpr(ValidatingExpr):

    def validate(self, val):
        pass


class UniqueExpr(ValidatingExpr):

    def __init__(self, columns):
        self.columns = columns

    def validate(self, val):
        pass


class UriExpr(ValidatingExpr):

    def validate(self, val):
        pass


class Uuid4Expr(ValidatingExpr):

    def validate(self, val):
        pass


class PositiveIntegerExpr(ValidatingExpr):

    def validate(self, val):
        pass


class UppercaseExpr(ValidatingExpr):

    def validate(self, val):
        pass


class LowercaseExpr(ValidatingExpr):

    def validate(self, val):
        pass


class IdenticalExpr(ValidatingExpr):

    def validate(self, val):
        pass



# Data-providing expressions #


# special case - column-ref, is a wrapper used for type-checking
class ColumnRef:

    def __init__(self, column):
        self.column = column





