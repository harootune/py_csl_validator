# stdlib
import re
import os
import pathlib
import urllib.parse as up

# third party
import validators as v

# local
from py_csl_validator.utils import expression_utils as eu


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
            valid = self.start <= len(val) <= self.end

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
        if self.columns:
            combination = [row[col] for col in self.columns]
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

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        valid = True
        try:
            uri = up.urlparse(val)
            uri.port  # checks for an invalid port because for some reason this is what it takes
        except ValueError:
            valid = False
        
        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


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

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        try:
            if ignore_case:
                valid = v.uuid(val.lower())
            else:
                valid = v.uuid(val)
        except v.ValidationFailure:
            valid = False
        
        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class PositiveIntegerExpr(ValidatingExpr):

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        valid = val >= 0

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class UppercaseExpr(ValidatingExpr):

    def validate(self, val, row, context, report_level='e', ignore_case=False):  # TODO: what to do if ignore case?
        valid = all([c.isupper() for c in val])

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class LowercaseExpr(ValidatingExpr):

    def validate(self, val, row, context, report_level='e', ignore_case=False):  # TODO: what to do if ignore case?
        valid = all([c.islower() for c in val])

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class IdenticalExpr(ValidatingExpr):

    def __init__(self):
        self.comparison = None

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        temp_val = val.lower() if ignore_case else val
        if self.comparison is None:
            self.comparison = temp_val
            valid = True
        else:
            valid = temp_val == self.comparison

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class FileExistsExpr(ValidatingExpr):

    def __init__(self, prefix):
        self.prefix = prefix

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        path = pathlib.Path(val)
        if self.prefix is not None and not path.is_absolute():
            curr_prefix = self.prefix.evaluate(row, context)
            path = pathlib.Path(curr_prefix).joinpath(path)

        if ignore_case:
            path = eu.find_path_from_caseless(path)
        
        valid = path.exists() if path else False

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid


class IntegrityCheckExpr(ValidatingExpr):

    def __init__(self, prefix, subfolder, folder_specification):
        self.prefix = prefix
        self.subfolder = subfolder if subfolder else 'content/'
        self.folder_specification = folder_specification

    def validate(self, val):
        pass


class ChecksumExpr(ValidatingExpr):

    def __init__(self, file_path, algorithm):
        self.file_path = file_path
        self.algorithm = algorithm

    def validate(self, val):
        pass


class FileCountExpr(ValidatingExpr):

    def __init__(self, file_path):
        self.file_path = file_path

    def validate(self, val, row, context, report_level='e', ignore_case=False):
        path = pathlib.Path(self.file_path.evaluate(row, context))
        if ignore_case:
            path = eu.find_path_from_caseless(path)
        
        valid = os.listdir(path) == val

        if report_level != 'n' and not valid:
            # TODO: error behavior
            pass

        return valid
            

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
        if isinstance(self.val, ColumnRef):
            return row[self.val.evaluate(row, context)]  # a column ref in a string provider should produce the text in said column
        if isinstance(self.val, DataExpr):
            return self.val.evaluate(row, context)
        else:
            return self.val
        

class ConcatExpr(DataExpr):

    def __init__(self, string_providers):
        self.string_providers = string_providers

    def evaluate(self, row, context):
        return ''.join([provider.evaluate(row, context) for provider in self.string_providers])


class NoExtExpr(DataExpr):

    def __init__(self, string_provider):
        self.string_provider = string_provider

    def evaluate(self, row, context):
        val = self.string_provider.evaluate(row, context)
        period_index = val.rfind('.')
        if period_index >= 0:
            return val[0:period_index]
        else:
            return val


class UriDecodeExpr(DataExpr):

    def __init__(self, string_provider, encoding):
        self.string_provider = string_provider
        self.encoding = encoding

    def evaluate(self, row, context):
        pass


class FileExpr(DataExpr):

    def __init__(self, prefix, file_path):
        self.prefix = prefix
        self.file_path = file_path

    def evaluate(self, row, context):
        if self.prefix is not None:
            curr_prefix = self.prefix.evaluate(row, context)
            curr_path = self.file_path.evalaute(row, context)
            
            path_obj = pathlib.Path(curr_path)
            if path_obj.is_absolute():
                return path_obj
            else:
                prefix_obj = pathlib.Path(curr_prefix)
                return prefix_obj.joinpath(path_obj)

        else:
            return pathlib.Path(self.file_path.evaluate(row, context))














