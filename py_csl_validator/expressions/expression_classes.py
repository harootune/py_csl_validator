# stdlib
import re
import os
import pathlib
import hashlib
import urllib.parse as up

# third party
import validators as v

# local
from py_csl_validator.utils import expression_utils as eu


# Schema

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


class ColumnRule:

    def __init__(self, col_vals, col_directives):
        self.col_vals = col_vals
        self.col_directives = col_directives

    def validate_column(self, key, row, context):
        no_case = self.col_directives['ignore_case']

        valid = True
        report_level = 'w' if self.col_directives['warning'] else 'e'  # replace characters with enum

        for expression in self.col_vals:  # TODO: handle parenthesized expressions
            if expression.validate(key, row, context, ignore_case=no_case):
                if self.col_directives['match_is_false']:
                    expression.report_error(report_level, key, row, context, ignore_case=no_case)
                    valid = False
            else:
                if (row[key] == '' and self.col_directives['optional']) or self.col_directives['match_is_false']:
                    continue
                else:
                    expression.report_error(report_level, key, row, context, ignore_case=no_case)
                    valid = False

        return valid


# Validating Expressions #
# Expressions which are directly used to validate the document #

class ValidatingExpr:

    def validate(self, key, row, context, ignore_case=False):
        raise NotImplementedError

    def report_error(self, report_level, key, row, context, ignore_case=False):
        raise NotImplementedError


class ColumnValidationExpr(ValidatingExpr):  # essentially a wrapper which makes checks for comb/noncomb expr easier

    def __init__(self, expression):
        self.expression = expression

    def validate(self, key, row, context, ignore_case=False):
        return self.expression.validate(key, row, context, ignore_case=ignore_case)
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        self.expression.report_error(report_level, key, row, context, ignore_case=ignore_case)


class ParenthesizedExpr(ValidatingExpr):

    def __init__(self, expressions):
        self.expressions = expressions

    def validate(self, key, row, context, ignore_case =False):
        return all(expr.validate(key, row, context, ignore_case=ignore_case) for expr in self.expressions)
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        for expression in self.expressions:
            if not expression.validate(key, row, context, ignore_case):
                expression.report_error(report_level, key, row, context, ignore_case)


class SingleExpr(ValidatingExpr):

    def __init__(self, expression, col_ref):
        self.expression = expression
        self.col_ref = col_ref

    def validate(self, key, row, context, ignore_case=False):
        if self.col_ref:
            return self.expression.validate(self.col_ref.evaluate(row, context),
                                            row,
                                            context,
                                            ignore_case=ignore_case)
        else:
            return self.expression.validate(key, row, context, ignore_case=ignore_case)
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        if self.col_ref:
            self.expression.report_error(report_level, self.col_ref.evaluate(row, context), row, context, ignore_case=ignore_case)
        else:
            self.expression.report_error(report_level, key, row, context, ignore_case=False)


class IsExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, key, row, context, ignore_case=False):
        if ignore_case:
            valid = row[key].lower() == self.comparison.evaluate(row, context).lower()
        else:
            valid = row[key] == self.comparison.evaluate(row, context)

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'IsExpr: {row[key]} not equivalent to {self.comparison.evaluate(row, context)}'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)
        

class AnyExpr(ValidatingExpr):

    def __init__(self, comparisons):
        self.comparisons = comparisons

    def validate(self, key, row, context, ignore_case=False):
        if ignore_case:
            valid = any([row[key].lower() == comparison.evaluate(row, context).lower() for comparison in self.comparisons])
        else:
            valid = any([row[key] == comparison.evaluate(row, context) for comparison in self.comparisons])

        return valid

    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'AnyExpr: {row[key]} not equivalent to any of the following:'
        for comparison in self.comparisons:
            msg += f' {comparison.evaluate(row, context)}'
        
        if ignore_case:
            msg += ' (case_ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class NotExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, key, row, context, ignore_case=False):
        if ignore_case:
            valid = row[key].lower() != self.comparison.evaluate(row, context).lower()
        else:
            valid = row[key] != self.comparison.evaluate(row, context)

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'NotExpr: {row[key]} is equivalent to {self.comparison.evaluate(row, context)}'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class InExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, key, row, context, ignore_case=False):
        if ignore_case:
            valid = self.comparison.evaluate(row, context).lower() in row[key].lower()
        else:
            valid = self.comparison.evaluate(row, context) in row[key]

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'InExpr: {row[key]} is a substring of {self.comparison.evaluate(row, context)}'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class StartsWithExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, key, row, context, ignore_case=False):
        if ignore_case:
            valid = re.match(f'^{self.comparison.evaluate(row, context).lower()}', row[key].lower())
        else:
            valid = re.match(f'^{self.comparison.evaluate(row, context)}', row[key])

        return valid

    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'StartsWithExpr: {row[key]} begins with {self.comparison.evaluate(row, context)}'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class EndsWithExpr(ValidatingExpr):

    def __init__(self, comparison):
        self.comparison = comparison

    def validate(self, key, row, context, ignore_case=False):
        if ignore_case:
            valid = re.match(f'{self.comparison.evaluate(row, context).lower()}$', row[key].lower())
        else:
            valid = re.match(f'{self.comparison.evaluate(row, context)}$', row[key])

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'EndsWithExpr: {row[key]} ends with {self.comparison.evaluate(row, context)}'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class RegExpExpr(ValidatingExpr):  # TODO: FIGURE OUT HOW TO EMULATE JAVA'S PATTERN CLASS

    def __init__(self, pattern):
        self.pattern = pattern

    def validate(self, val, context):
        pass


class RangeExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start if start != '*' else -float('inf')
        self.end = end if end != '*' else float('inf')

    def validate(self, key, row, context, ignore_case=False):
        try:
            valid = self.start <= float(row[key]) <= self.end
        except ValueError:
            valid = False

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'RangeExpr: {row[key]} is not a number between {self.start} and {self.end}'

        context.errors[context.row_count][key][report_level].append(msg)


class LengthExpr(ValidatingExpr):

    def __init__(self, start, end):
        self.start = start if start != '*' else -float('inf')
        self.end = end if end != '*' else float('inf')

    def validate(self, key, row, context, ignore_case=False):
        if not self.end:
            valid = len(row[key]) == self.start
        else:
            valid = self.start <= len(row[key]) <= self.end

        return valid

    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'LengthExpr: Length of {row[key]} is not between {self.start} and {self.end}'

        context.errors[context.row_count][key][report_level].append(msg)


class EmptyExpr(ValidatingExpr):  # TODO: Pass for behavior

    def validate(self, key, row, context, ignore_case=False):
        valid = row[key] == ''

        return valid

    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'EmptyExpr: Column is not empty'

        context.errors[context.row_count][key][report_level].append(msg)


class NotEmptyExpr(ValidatingExpr):  # TODO: Pass for behavior

    def validate(self, key, row, context, ignore_case=False):
        valid = row[key] != ''

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'NotEmptyExpr: Column is empty'

        context.errors[context.row_count][key][report_level].append(msg)
        

class UniqueExpr(ValidatingExpr):

    def __init__(self, columns):
        self.columns = columns
        self.seen = set()

    def validate(self, key, row, context, ignore_case=False):
        if self.columns:
            combination = [row[col] for col in self.columns]
            if ignore_case:
                combination = [val.lower() for val in combination]

            if combination not in self.seen:
                valid = True
                self.seen.add(combination)
            else:
                valid = False
        else:
            val = row[key]
            if ignore_case:
                val = val.lower()

            if val not in self.seen:
                valid = True
                self.seen.add(val)
            else:
                valid = False

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = 'UniqueExpr:'
        if self.columns:
            msg = ' Combination ['
            for col in self.columns:
                msg += f'{row[col]}, '
            msg += '] is not unique'
        else:
            msg += f' Value {row[key]} is not unique'
        
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class UriExpr(ValidatingExpr):

    def validate(self, key, row, context, ignore_case=False):
        valid = True
        try:
            uri = up.urlparse(row[key])
            uri.port  # checks for an invalid port because for some reason this is what it takes
        except ValueError:
            valid = False

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'UriExpr: {row[key]} could not be parsed as a uri.'

        context.errors[context.row_count][key][report_level].append(msg)


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

    def validate(self, key, row, context, ignore_case=False):
        try:
            if ignore_case:
                valid = v.uuid(row[key].lower())
            else:
                valid = v.uuid(row[key])
        except v.ValidationFailure:
            valid = False

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'Uuid4Expr: {row[key]} is not a valid UUID4'

        context.errors[context.row_count][key][report_level].append(msg)


class PositiveIntegerExpr(ValidatingExpr):

    def validate(self, key, row, context, ignore_case=False):
        try:
            val = float(row[key])
            valid = val.is_integer() and val >= 0
        except ValueError: 
            valid = False
        
        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'PositiveIntegerExpr: {row[key]} is not a positive integer'

        context.errors[context.row_count][key][report_level].append(msg)
            

class UppercaseExpr(ValidatingExpr):

    def validate(self, key, row, context, ignore_case=False):  # TODO: what to do if ignore case?
        valid = all([c.isupper() for c in row[key]])

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'UppercaseExpr: {row[key]} is not all uppercase'

        context.errors[context.row_count][key][report_level].append(msg)


class LowercaseExpr(ValidatingExpr):

    def validate(self, key, row, context, ignore_case=False):  # TODO: what to do if ignore case?
        valid = all([c.islower() for c in row[key]])

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'UppercaseExpr: {row[key]} is not all uppercase'

        context.errors[context.row_count][key][report_level].append(msg)
    

class IdenticalExpr(ValidatingExpr):

    def __init__(self):
        self.comparison = None

    def validate(self, key, row, context, ignore_case=False):
        temp_val = row[key].lower() if ignore_case else row[key]
        if self.comparison is None:
            self.comparison = temp_val
            valid = True
        else:
            valid = temp_val == self.comparison

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        msg = f'IdenticalExpr: {row[key]} deviates from previous column values'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class FileExistsExpr(ValidatingExpr):

    def __init__(self, prefix):
        self.prefix = prefix

    def validate(self, key, row, context, ignore_case=False):
        path = pathlib.Path(row[key])
        if self.prefix is not None and not path.is_absolute():
            curr_prefix = self.prefix.evaluate(row, context)
            path = pathlib.Path(curr_prefix).joinpath(path)

        if ignore_case:
            path = eu.find_path_from_caseless(path)
        
        valid = path.exists() if path is not None else False

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        path = pathlib.Path(row[key])
        if self.prefix is not None and not path.is_absolute():
            curr_prefix = self.prefix.evaluate(row, context)
            path = pathlib.Path(curr_prefix).joinpath(path)
        
        msg = f'FileExistsExpr: {path} is not an extant path'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)


class IntegrityCheckExpr(ValidatingExpr):

    def __init__(self, prefix, subfolder, folder_specification):
        self.prefix = prefix if prefix else ''
        self.subfolder = subfolder if subfolder else 'content'
        self.folder_specification = folder_specification

    def validate(self, key, row, context, ignore_case=False):
        path = pathlib.path(row[key])
        if self.prefix is not None and not path.is_absolute():
            curr_prefix = self.prefix.evaluate(row, context)
            path = pathlib.Path(curr_prefix).joinpath(path)

        subfolder = self.subfolder if subfolder == 'content' else self.subfolder.evaluate(row, context)

        path = path.joinpath(subfolder)

        # TODO: Figure out how to differentiate between folders and files with os
        # https://pythonexamples.org/python-check-if-path-is-file-or-directory/
    



class ChecksumExpr(ValidatingExpr):

    def __init__(self, file_path, algorithm):
        self.file_path = file_path
        self.algorithm = algorithm.lower()

    def validate(self, key, row, context, ignore_case=False):
        if self.algorithm not in hashlib.algorithms_available:
            return False
            # TODO: Move to load-time errors
        
        path = pathlib.Path(self.file_path.evaluate(row, context))
        if ignore_case:
            path = eu.find_path_from_caseless(path)
            if not path:
                return False
        
        try:
            with open(path, mode='rb') as infile:
                hash_alg = hashlib.new(self.algorithm)
                file_bytes = infile.read()
                hash_alg.update(file_bytes)
                file_hash = hash_alg.hexdigest()

                checksum = row[key]
                if ignore_case:
                    checksum = checksum.lower()
                
                valid = file_hash == checksum
        except FileNotFoundError as e:
            valid = False
        
        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        if self.algorithm not in hashlib.algorithms_available:
            msg = f'ChecksumExpr: {self.algorithm} not available with this interpeter'
            # TODO: Move to load-time errors
        else:
            path = pathlib.Path(self.file_path.evaluate(row, context))
            if ignore_case:
                path = eu.find_path_from_caseless(path)
            
            if path is None:
                msg = f'ChecksumExpr: {self.file_path.evaluate(row, context)} does not correspond to a case-ignored path'
            elif not path.exists():
                msg =f'ChecksumExpr: {"".join(path.parts)} not found in filesystem'
                if ignore_case:
                    msg += ' (case ignored)'
            else:
                msg = f'ChecksumExpr: {"".join(path.parts)} {self.algorithm} checksum does not match.'

            context.errors[context.row_count][key][report_level].append(msg)
            
                
class FileCountExpr(ValidatingExpr):

    def __init__(self, file_path):
        self.file_path = file_path

    def validate(self, key, row, context, ignore_case=False):
        path = pathlib.Path(self.file_path.evaluate(row, context))
        if ignore_case:
            path = eu.find_path_from_caseless(path)
            if path is None:
                return False
        
        valid = len(os.listdir(path)) == float(row[key])

        return valid
    
    def report_error(self, report_level, key, row, context, ignore_case=False):
        path = pathlib.Path(self.file_path.evaluate(row, context))
        if ignore_case:
            path = eu.find_path_from_caseless(path)
            if path is None:
                msg = f'FileCountExpr: {self.file_path.evaluate(row, context)} does not correspond to a case-ignored path'

        msg = f'FileCountExpr: {self.file_path.evaluate(row, context)} did not contain {row[key]} files at check time'
        if ignore_case:
            msg += ' (case ignored)'
        
        context.errors[context.row_count][key][report_level].append(msg)
            

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
            curr_path = self.file_path.evaluate(row, context)
            
            path_obj = pathlib.Path(curr_path)
            if path_obj.is_absolute():
                return path_obj
            else:
                prefix_obj = pathlib.Path(curr_prefix)
                return prefix_obj.joinpath(path_obj)

        else:
            return pathlib.Path(self.file_path.evaluate(row, context))














