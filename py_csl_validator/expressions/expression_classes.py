# stdlib
import re


class Schema:  # TODO: Should this be a ValidatingExpr?

    def __init__(self, prolog, body):
        self.prolog = prolog
        self.body = body


# Prolog #
class Prolog:

    def __init__(self, version, global_directives):
        self.version = version
        self.global_directives = global_directives


class GlobalDirectives:

    def __init__(self, stack):

        self.directives = {
            'separator': None,
            'quoted': False,
            'total_columns': None,
            'permit_empty': False,
            'no_header': False,
            'ignore_column_name_case': False,
        }

        for el in stack:
            self.directives[el[0]] = el[1]

        if self.directives['separator'] == 'TAB':
            self.directives['separator'] = '\t'

        if self.directives['no_header'] and self.directives['ignore_column_name_case']:
            # TODO: Raise an error
            pass
# Body #


class Body:

    def __init__(self, column_defs):
        self.column_defs = column_defs


class ColumnDefinition:

    def __init__(self, col_name, col_rule):
        self.name = col_name
        self.rule = col_rule


class ValidatingExpr:

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        raise NotImplementedError


class ColumnRule(ValidatingExpr):

    def __init__(self, col_vals, col_directives):
        self.col_vals = col_vals
        self.col_directives = col_directives

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        no_case = ignore_case or self.col_directives['ignore_case']  # allows for us to manually set case directive

        valid = True
        for expression in self.col_vals:  # TODO: handle parenthesized expressions
            if not expression.validate(val, row, context, report_level=report_level, ignore_case=no_case):
                if val == '' and self.col_directives['optional']:  # TODO: match_is_false and optional?
                    continue
                else:
                    # TODO: Log an error or warning in context
                    valid = False
            elif self.col_directives['match_is_false']:
                # TODO: Log an error or warning in context
                valid = False

        return valid


class ColumnValidationExpr(ValidatingExpr):  # essentially a wrapper which makes checks for comb/noncomb expr easier

    def __init__(self, expression):
        self.expression = expression

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        return self.expression.validate(val, row, context, report_level=report_level, ignore_case=ignore_case)


class ParenthesizedExpr(ValidatingExpr):

    def __init__(self, expressions):
        self.expressions = expressions

    def validate(self, val, row, context, report_level='e', ignore_case =False):
        return all(expr.validate(val, row, context, report_level=report_level, ignore_case=ignore_case) for expr in self.expressions)


class SingleExpr(ValidatingExpr):

    def __init__(self, expression, col_ref):
        self.expression = expression
        self.col_ref = col_ref

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if self.col_ref:
            return self.expression.validate(row[self.col_ref.evaluate(row, context)],
                                            row,
                                            context,
                                            report_level=report_level,
                                            ignore_case=ignore_case)
        else:
            return self.expression.validate(val, row, context, ignore_case=ignore_case)


class IsExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if ignore_case:
            valid = val.lower() == self.comparison.evaluate(row, context).lower()
        else:
            valid = val == self.comparison.evaluate(row, context)

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class AnyExpr(ValidatingExpr):

    def __init__(self, comparisons):
        self.comparisons = comparisons

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if ignore_case:
            valid = any([val.lower() == comparison.evaluate(row, context).lower() for comparison in self.comparisons])
        else:
            valid = any([val == comparison.evaluate(row, context) for comparison in self.comparisons])

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class NotExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if ignore_case:
            valid = val.lower() != self.comparison.evaluate(row, context).lower()
        else:
            valid = val != self.comparison.evaluate(row, context)

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class InExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if ignore_case:
            valid = self.comparison.evaluate(row, context).lower() in val.lower()
        else:
            valid = self.comparison.evaluate(row, context) in val

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class StartsWithExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if ignore_case:
            valid = re.match(f'^{self.comparison.evaluate(row, context).lower()}', val.lower())
        else:
            valid = re.match(f'^{self.comparison.evaluate(row, context)}', val)

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class EndsWithExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if ignore_case:
            valid = re.match(f'{self.comparison.evaluate(row, context).lower()}$', val.lower())
        else:
            valid = re.match(f'{self.comparison.evaluate(row, context)}$', val)

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class RegExpExpr(ValidatingExpr):

    def __init__(self, pattern):
        self.pattern = pattern

    def validate(self, val, context):
        pass


class RangeExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start if start != '*' else -float('inf')
        self.end = end if end != '*' else float('inf')

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        valid = self.start <= val <= self.end

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class LengthExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start if start != '*' else -float('inf')
        self.end = end if end != '*' else float('inf')

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if not self.end:
            valid = len(val) == self.start
        else:
            valid = self.start <= len(val) <= start.end

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class EmptyExpr(ValidatingExpr):  # TODO: Pass for behavior

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        valid = False if val else True

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass


class NotEmptyExpr(ValidatingExpr):  # TODO: Pass for behavior

    def validate(self, val):
        pass


class UniqueExpr(ValidatingExpr):

    def __init__(self, columns):
        self.columns = columns
        self.seen = set()

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        if columns:
            combination = [row[col] for col in columns]
            if combination not in self.seen:
                valid = True
                self.seen.add(combination)
            else:
                valid = False
        else:
            if val not in self.seen:
                valid = True
                self.seen.add(val)
            else:
                valid = False

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class UriExpr(ValidatingExpr):

    def validate(self, val):
        pass


class XsdDateTimeExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class XsdDateTimeWithTimezoneExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class XsdDateExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class XsdTimeExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class UkDateExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class DateExpr(ValidatingExpr):

    def __init__(self, year, month, day, start, end):
        self.year = year
        self.month = month
        self.day = day
        self.start = start
        self.end = end

    def validate(self, val):
        pass


class PartialUkDateExpr(ValidatingExpr):

    def validate(self, val):
        pass


class PartialDateExpr(ValidatingExpr):

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

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


class FileExistsExpr(ValidatingExpr):

    def __init__(self, prefix):
        self.prefix = prefix

    def validate(self, val):
        pass


class IntegrityCheckExpr(ValidatingExpr):

    def __init__(self, prefix, subfolder, folder_specification):
        self.prefix = prefix
        self.subfolder = subfolder if subfolder else 'content/'
        self.folder_specification = folder_specification

    def validate(self, val):
        pass


class ChecksumExpr(ValidatingExpr):

    def __init__(self, file, algorithm):
        self.file = file
        self.algorithm = algorithm

    def validate(self, val):
        pass


class FileCountExpr(ValidatingExpr):

    def __init__(self, file):
        self.file = file

    def validate(self, val):
        pass


class OrExpr(ValidatingExpr):

    def __init__(self, expressions):
        self.expressions = expressions

    def validate(self, val):
        pass


class AndExpr(ValidatingExpr):

    def __init__(self, expressions):
        self.expressions = expressions

    def validate(self, val):
        pass


class IfExpr(ValidatingExpr):

    def __init__(self, condition, if_clause, else_clause):
        self.condition = condition
        self.if_clause = if_clause
        self.else_clause = else_clause

    def validate(self, val):
        pass


class IfClause(ValidatingExpr):

    def __init__(self, expressions):
        self.expressions = expressions

    def validate(self, val):
        pass


class SwitchExpr(ValidatingExpr):

    def __init__(self, cases, else_clause):
        self.cases = cases
        self.else_clause = else_clause

    def validate(self, val):
        pass


class SwitchCaseExpr(ValidatingExpr):

    def __init__(self, condition, if_clause):
        self.condition = condition
        self.if_clause = if_clause

    def validate(self, val):
        pass

# Column directives #


class ColumnDirectives:

    def __init__(self, stack):
        self.directives = {
            'optional': False,
            'match_is_false': False,
            'ignore_case': False,
            'warning': False
        }

        for el in stack:
            self.directives[el[0]] = el[1]


# Data-providing expressions #


class DataExpr:

    def evaluate(self, row, context):
        raise NotImplementedError


# special case - column-ref, is a wrapper used for type-checking
class ColumnRef(DataExpr):

    def __init__(self, column):
        self.column = column

    def evaluate(self, row, context):
        return self.column.lower() if context.global_directives['ignore_column_name_case'] else self.column


class StringProvider(DataExpr):

    def __init__(self, val):
        self.val = val

    def evaluate(self, row, context):
        pass


class ConcatExpr(DataExpr):

    def __init__(self, string_providers):
        self.string_providers = string_providers

    def evaluate(self, row, context):
        pass


class NoExtExpr(DataExpr):

    def __init__(self, string_provider):
        self.string_provider = string_provider

    def evaluate(self, row, context):
        pass


class UriDecodeExpr(DataExpr):

    def __init__(self, string_provider, encoding):
        self.string_provider = string_provider
        self.encoding = encoding

    def evaluate(self, row, context):
        pass


class FileExpr(DataExpr):

    def __init__(self, prefix, file):
        self.prefix = prefix
        self.file = file

    def evaluate(self, row, context):
        pass














