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


class SingleExpr(ValidatingExpr):

    def __init__(self, expression, col_ref):
        self.expression = expression
        self.col_Ref = col_ref

    def validate(self, val):
        pass


class IsExpr(ValidatingExpr):

    def __init__(self, string):
        self.string = string

    def validate(self, val):
        pass


# Data-providing expressions #


# special case - column-ref, is a wrapper used for type-checking
class ColumnRef:

    def __init__(self, column):
        self.column = column





