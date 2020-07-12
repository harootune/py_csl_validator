# local
from py_csl_validator.expressions import expression_classes as ec


class ExpressionIndex:
    instance = None

    @staticmethod
    def get_index():
        """Enables singleton interaction with ExpressionIndex"""
        if ExpressionIndex.instance is None:
            ExpressionIndex.instance = ExpressionIndex()
        return ExpressionIndex.instance

    def call_expression(self, visitor, tree):
        return getattr(self, tree.data, self.__default__)(visitor)

    def __default__(self, visitor):
        pass

    def schema(self, visitor):
        body = visitor.stack.pop()
        global_directives = visitor.stack.pop()

        visitor.stack.append(ec.Schema(body, global_directives))

    # prolog #

    def global_directives(self, visitor):
        directives = []
        while visitor.stack:
            if isinstance(visitor.stack[-1], ec.GlobalDirective):
                directives.append(visitor.stack.pop())
            else:
                break

        visitor.stack.append(ec.GlobalDirectives(directives))

    def separator_directive(self, visitor):
        separator = visitor.stack.pop()

        visitor.stack.append(ec.SeparatorDirective(separator))

    def total_columns_directive(self, visitor):
        num_columns = visitor.stack.pop()

        visitor.stack.append(ec.TotalColumnsDirective(num_columns))

    # def permit_empty_directive(self, visitor)

    # def quoted_directive(self, visitor):

    # def no_header_directive(self, visitor):

    # def ignore_column_name_case_directive(self, visitor):


    # body #

    def body(self, visitor):
        column_defs = []
        while visitor.stack:
            if isinstance(visitor.stack[-1], ec.ColumnDefinition):
                column_defs.append(visitor.stack.pop())
            else:
                break

        visitor.stack.append(ec.Body(column_defs))

    def column_definition(self, visitor):
        col_rule = visitor.stack.pop()
        col_name = visitor.stack.pop()

        visitor.stack.append(ec.ColumnDefinition(col_name, col_rule))

    def column_rule(self, visitor):
        col_directives = visitor.stack.pop()
        col_vals = []
        while visitor.stack:
            if isinstance(visitor.stack[-1], ec.ColumnValidationExpr):
                col_vals.append(visitor.stack.pop())
            else:
                break

        visitor.stack.append(ec.ColumnRule(col_vals, col_directives))

    def column_validation_expr(self, visitor):
        expression = visitor.stack.pop()  # TODO: improve this vocab?

        visitor.stack.append(ec.ColumnValidationExpr(expression))

    def single_expr(self, visitor):
        expression = visitor.stack.pop()
        col_ref = None
        if visitor.stack:
            if isinstance(visitor.stack[-1], ec.ColumnRef):
                col_ref = visitor.stack.pop()

        visitor.stack.append(ec.SingleExpr(expression, col_ref))

    def is_expr(self, visitor):
        string = visitor.stack.pop()

        visitor.stack.append(ec.IsExpr(string))

    # Data-providing expressions #

    def column_ref(self, visitor):
        column = visitor.stack.pop()

        visitor.stack.append(ec.ColumnRef(column))