# third party
from lark import Tree, Token

# local
import py_csl_validator.expressions.expression_classes as ec
from .csl_visitor import CslVisitor


class CslVisitor1_2(CslVisitor):

    # custom methods #

    def start(self, stack):
        return stack.pop()

    def schema(self, stack):
        body = stack.pop()
        prolog = stack.pop()

        return ec.Schema(prolog, body)

    # prolog #
    def prolog(self, stack):
        global_directives = stack.pop()
        version = stack.pop()

        return ec.Prolog(version, global_directives)

    # global directives

    def global_directives(self, stack):
        stack.reverse()

        return ec.GlobalDirectives(stack)

    def separator_directive(self, stack):
        separator = stack.pop()

        return 'separator', separator

    def total_columns_directive(self, stack):
        num_columns = stack.pop()

        return 'total_columns', num_columns

    def permit_empty_directive(self, *args):
        return 'permit_empty', True

    def quoted_directive(self, *args):
        return 'quoted', True

    def no_header_directive(self, *args):
        return 'no_header', True

    def ignore_column_name_case_directive(self, *args):
        return 'ignore_column_name_case', True

    # body #

    def body(self, stack):
        stack.reverse()

        return ec.Body(stack)

    def body_part(self, stack):
        # filter comments
        for element in stack:
            if isinstance(element, ec.ColumnDefinition):
                return element

    def column_definition(self, stack):
        col_rule = stack.pop()
        col_name = stack.pop()

        return ec.ColumnDefinition(col_name, col_rule)

    def column_rule(self, stack):
        col_directives = stack.pop()
        stack.reverse()

        return ec.ColumnRule(stack, col_directives)

    def column_validation_expr(self, stack):
        expression = stack.pop()  # TODO: improve this vocab?

        return ec.ColumnValidationExpr(expression)

    def single_expr(self, stack):
        expression = stack.pop()
        col_ref = None
        if stack:
            col_ref = stack.pop()

        return ec.SingleExpr(expression, col_ref)

    def external_single_expr(self, stack):
        return self.single_expr(stack)

    def parenthesized_expr(self, stack):
        stack.reverse()

        return ec.ParenthesizedExpr(stack)

    def is_expr(self, stack):
        comparison = stack.pop()

        return ec.IsExpr(comparison)

    def any_expr(self, stack):
        stack.reverse()

        return ec.AnyExpr(stack)

    def not_expr(self, stack):
        comparison = stack.pop()

        return ec.NotExpr(comparison)

    def in_expr(self, stack):
        comparison = stack.pop()

        return ec.InExpr(comparison)

    def starts_with_expr(self, stack):
        comparison = stack.pop()

        return ec.StartsWithExpr(comparison)

    def ends_with_expr(self, stack):
        comparison = stack.pop()

        return ec.EndsWithExpr(comparison)

    def reg_exp_expr(self, stack):
        pattern = stack.pop()

        return ec.RegExpExpr(pattern)

    def range_expr(self, stack):
        end = stack.pop()
        start = stack.pop()

        return ec.RangeExpr(start, end)

    def length_expr(self, stack):
        start = stack.pop()
        end = None
        if stack:
            end, start = start, stack.pop()

        return ec.LengthExpr(start, end)

    def empty_expr(self, *args):
        return ec.EmptyExpr()

    def not_empty_expr(self, *args):
        return ec.NotEmptyExpr()

    def unique_expr(self, stack):
        stack.reverse()

        return ec.UniqueExpr(stack)

    def uri_expr(self, *args):
        return ec.UriExpr()

    def xsd_datetime_expr(self, stack):
        end = stack.pop() if stack else None
        start = stack.pop() if stack else None

        return ec.XsdDateTimeExpr(start, end)

    def xsd_datetime_with_timezone_expr(self, stack):
        end = stack.pop() if stack else None
        start = stack.pop() if stack else None

        return ec.XsdDateTimeWithTimezoneExpr(start, end)

    def xsd_date_expr(self, stack):
        end = stack.pop() if stack else None
        start = stack.pop() if stack else None

        return ec.XsdDateExpr(start, end)

    def xsd_time_expr(self, stack):
        end = stack.pop() if stack else None
        start = stack.pop() if stack else None

        return ec.XsdTimeExpr(start, end)


    def uk_date_expr(self, stack):
        end = stack.pop() if stack else None
        start = stack.pop() if stack else None

        return ec.UkDateExpr(start, end)

    def date_expr(self, stack):  # TODO: redo to account for string providers
        if len(stack) == 5:
            end = stack.pop()
            start = stack.pop()
        else:
            end = None
            start = None

        day = stack.pop()
        month = stack.pop()
        year = stack.pop()

        return ec.DateExpr(year, month, day, start, end)

    def partial_uk_date_expr(self, *args):
        return ec.PartialUkDateExpr()

    def partial_date_expr(self, stack):
        day = stack.pop()
        month = stack.pop()
        year = stack.pop()

        return ec.PartialDateExpr(year, month, day)

    def uuid4_expr(self, *args):
        return ec.Uuid4Expr()

    def positive_integer_expr(self, *args):
        return ec.PositiveIntegerExpr()

    def uppercase_expr(self, *args):
        return ec.UppercaseExpr()

    def lowercase_expr(self, *args):
        return ec.LowercaseExpr()

    def identical_expr(self, *args):
        return ec.IdenticalExpr()

    def file_exists_expr(self, stack):
        prefix = stack.pop() if stack else None

        return ec.FileExistsExpr(prefix)

    def integrity_check_expr(self, stack):
        folder_specification = stack.pop()
        subfolder = None
        prefix = None
        if stack:
            prefix = stack.pop()

            if stack:
                prefix, subfolder = stack.pop(), prefix

        return ec.IntegrityCheckExpr(prefix, subfolder, folder_specification)

    def checksum_expr(self, stack):
        algorithm = stack.pop()
        file = stack.pop()

        return ec.ChecksumExpr(file, algorithm)

    def file_count_expr(self, stack):
        file = stack.pop()

        return ec.FileCountExpr(file)

    def or_expr(self, stack):
        stack.reverse()

        return ec.OrExpr(stack)

    def and_expr(self, stack):
        stack.reverse()

        return ec.AndExpr(stack)

    def if_expr(self, stack):
        else_clause = None
        if_clause = stack.pop()

        if isinstance(stack[-1], ec.IfClause):
            else_clause, if_clause = if_clause, stack.pop()

        condition = stack.pop()

        return ec.IfExpr(condition, if_clause, else_clause)

    def if_clause(self, stack):
        stack.reverse()

        return ec.IfClause(stack)

    def switch_expr(self, stack):
        else_clause = stack.pop() if isinstance(stack[-1], ec.IfClause) else None
        stack.reverse()

        return ec.SwitchExpr(stack, else_clause)

    def switch_case_expr(self, stack):
        if_clause = stack.pop()
        condition = stack.pop()

        return ec.SwitchCaseExpr(condition, if_clause)

    # column directives #
    def column_directives(self, stack):
        stack.reverse()

        return ec.ColumnDirectives(stack)

    def optional_directive(self, *args):
        return 'optional', True

    def match_is_false_directive(self, *args):
        return 'match_is_false', True

    def ignore_case_directive(self, *args):
        return 'ignore_case', True

    def warning_directive(self, *args):
        return 'warning', True

    # Data-providing expressions #

    def string_provider(self, stack):
        val = stack.pop()

        return ec.StringProvider(val)

    def column_ref(self, stack):
        column = stack.pop()

        return ec.ColumnRef(column)

    def concat_expr(self, stack):
        stack.reverse()

        return ec.ConcatExpr(stack)

    def no_ext_expr(self, stack):
        string_provider = stack.pop()

        return ec.NotExpr(string_provider)

    def uri_decode_expr(self, stack):
        encoding = None
        string_provider = stack.pop()

        if stack:
            encoding, string_provider = string_provider, stack.pop()

        return ec.UriDecodeExpr(string_provider, encoding)

    def file_expr(self, stack):
        file = stack.pop()
        prefix = None
        if stack:
            prefix = stack.pop()

        return ec.FileExpr(prefix, file)




