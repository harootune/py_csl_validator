# third party
from lark import Tree, Token

# local
import py_csl_validator.expressions.expression_classes as ec


class CslVisitor:
    counted_expr = ['parenthesized_expr',
                    'concat_expr',
                    'uri_decode_expr']

    def __init__(self):
        self.stack = []

    def visit(self, tree):
        for child in tree.children:
            if isinstance(child, Token):
                self.stack.append(child.value)
            elif isinstance(child, Tree):
                self.visit(child)

        # handle parenthesized expressions
        # in most cases we can avoid explicit counts by exploiting grammatical structure
        # however, we must do so to properly handle certain instructions
        if tree.data in self.counted_expr:
            self._call_counted_expression(tree)
        else:
            self._call_expression(tree)

    def _call_expression(self, tree):
        getattr(self, tree.data, self.__default__)()

    def _call_counted_expression(self, tree):
        getattr(self, tree.data, self.__default__)(len(tree.children))

    def __default__(self, *args):
        pass

    ## stack operations ##

    def schema(self):
        body = self.stack.pop()
        prolog = self.stack.pop()

        self.stack.append(ec.Schema(prolog, body))

    def parenthesized_expr(self, count):
        expressions = [self.stack.pop() for i in range(count)]

        self.stack.append(ec.ParenthesizedExpr(expressions))




    # prolog #
    def prolog(self):
        global_directives = self.stack.pop()
        version = self.stack.pop()

        self.stack.append(ec.Prolog(version, global_directives))

    def global_directives(self):
        directives = []
        while self.stack:
            if isinstance(self.stack[-1], ec.GlobalDirective):
                directives.append(self.stack.pop())
            else:
                break

        self.stack.append(ec.GlobalDirectives(directives))

    def separator_directive(self):
        separator = self.stack.pop()

        self.stack.append(ec.SeparatorDirective(separator))

    def total_columns_directive(self):
        num_columns = self.stack.pop()

        self.stack.append(ec.TotalColumnsDirective(num_columns))

    # def permit_empty_directive(self)

    # def quoted_directive(self):

    # def no_header_directive(self):

    # def ignore_column_name_case_directive(self):

    # body #

    def body(self):
        column_defs = []
        while self.stack:
            if isinstance(self.stack[-1], ec.ColumnDefinition):
                column_defs.append(self.stack.pop())
            else:
                break

        self.stack.append(ec.Body(column_defs))

    def column_definition(self):
        col_rule = self.stack.pop()
        col_name = self.stack.pop()

        self.stack.append(ec.ColumnDefinition(col_name, col_rule))

    def column_rule(self):
        col_directives = self.stack.pop()
        col_vals = []
        while self.stack:
            if isinstance(self.stack[-1], ec.ColumnValidationExpr):
                col_vals.append(self.stack.pop())
            else:
                break

        self.stack.append(ec.ColumnRule(col_vals, col_directives))

    def column_validation_expr(self):
        expression = self.stack.pop()  # TODO: improve this vocab?

        self.stack.append(ec.ColumnValidationExpr(expression))

    def single_expr(self):
        expression = self.stack.pop()
        col_ref = None
        if self.stack:
            if isinstance(self.stack[-1], ec.ColumnRef):
                col_ref = self.stack.pop()

        self.stack.append(ec.SingleExpr(expression, col_ref))

    def is_expr(self):
        comparison = self.stack.pop()

        self.stack.append(ec.IsExpr(comparison))

    def any_expr(self):
        comparisons = []
        while self.stack:
            if isinstance(self.stack[-1], (str, int, ec.ColumnRef)):
                comparisons.append(self.stack.pop())
            else:
                break

        self.stack.append(ec.AnyExpr(comparisons))

    def not_expr(self):
        comparison = self.stack.pop()

        self.stack.append(ec.NotExpr(comparison))

    def in_expr(self):
        comparison = self.stack.pop()

        self.stack.append(ec.InExpr(comparison))

    def starts_with_expr(self):
        comparison = self.stack.pop()

        self.stack.append(ec.StartsWithExpr(comparison))

    def ends_with_expr(self):
        comparison = self.stack.pop()

        self.stack.append(ec.EndsWithExpr(comparison))

    def reg_exp_expr(self):
        pattern = self.stack.pop()

        self.stack.append(ec.RegExpExpr(pattern))

    def range_expr(self):
        end = self.stack.pop()
        start = self.stack.pop()

        self.stack.append(ec.RangeExpr(start, end))

    def length_expr(self):
        start = self.stack.pop()
        end = None
        if self.stack:
            if isinstance(self.stack[-1], (str, int)):
                end, start = start, self.stack.pop()

        self.stack.append(ec.LengthExpr(start, end))

    def empty_expr(self):
        self.stack.append(ec.EmptyExpr())

    def not_empty_expr(self):
        self.stack.append(ec.NotEmptyExpr())

    def unique_expr(self):
        columns = []
        while self.stack:
            if isinstance(self.stack[-1], ec.ColumnRef):
                columns.append(self.stack.pop())
            else:
                break

        self.stack.append(ec.UniqueExpr(columns))

    def uri_expr(self):
        self.stack.append(ec.UriExpr)

    # def xsd_datetime_expr(self):

    # def xsd_datetime_with_timezone_expr(self):

    # def xsd_date_expr(self):

    # def xsd_time_expr(self):

    # uk_date_expr(self):

    # date_expr(self):

    # partial_uk_date_expr(self):

    # partial_date_expr(self):

    def uuid4_expr(self):
        self.stack.append(ec.Uuid4Expr())

    def positive_integer_expr(self):
        self.stack.append(ec.PositiveIntegerExpr())

    def uppercase_expr(self):
        self.stack.append(ec.UppercaseExpr())

    def lowercase_expr(self):
        self.stack.append(ec.LowercaseExpr())

    def identical_expr(self):
        self.stack.append(ec.IdenticalExpr())

    def external_single_expr(self):
        self.single_expr()

    def file_exists_expr(self):
        prefix = None
        if isinstance(self.stack[-1], (str, ec.ColumnRef)):
            prefix = self.stack.pop()

        self.stack.append(ec.FileExistsExpr(prefix))

    def integrity_check_expr(self):
        folder_specification = self.stack.pop()
        subfolder = None
        prefix = None
        if self.stack:
            if isinstance(self.stack[-1], (str, ec.ColumnRef)):
                prefix = self.stack.pop()

                if self.stack:
                    if isinstance(self.stack[-1], (str, ec.ColumnRef)):
                        prefix, subfolder = self.stack.pop(), prefix

        self.stack.append(ec.IntegrityCheckExpr(prefix, subfolder, folder_specification))

    def checksum_expr(self):
        algorithm = self.stack.pop()
        file = self.stack.pop()

        self.stack.append(ec.ChecksumExpr(file, algorithm))

    def file_count_expr(self):
        file = self.stack.pop()

        self.stack.append(ec.FileCountExpr(file))



    # Data-providing expressions #

    def string_provider(self):
        val = self.stack.pop()

        self.stack.append(ec.StringProvider(val))

    def column_ref(self):
        column = self.stack.pop()

        self.stack.append(ec.ColumnRef(column))

    def concat_expr(self, count):
        string_providers = [self.stack.pop() for i in range(count)]

        self.stack.append(ec.ConcatExpr(string_providers))

    def no_ext_expr(self):
        string_provider = self.stack.pop()

        self.stack.append(ec.NotExpr(string_provider))

    def uri_decode_expr(self, count):
        encoding = None
        string_provider = self.stack.pop()

        if count == 2:
            encoding, string_provider = string_provider, self.stack.pop()

        self.stack.append(ec.UriDecodeExpr(string_provider, encoding))

    def file_expr(self):
        file = self.stack.pop()
        prefix = None
        if self.stack:
            if isinstance(self.stack[-1], ec.StringProvider):
                prefix = self.stack.pop()

        self.stack.append(ec.FileExpr(prefix, file))




