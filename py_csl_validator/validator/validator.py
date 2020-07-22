# stdlib
import csv

# local
import py_csl_validator.utils.validator_utils as vu


class CslValidator:

    def __init__(self, schema_file):
        version = vu.find_version_number(schema_file)
        visitor = vu.find_visitor(version)
        parser = vu.find_parser(version)

        with open(schema_file, mode='r', newline='', encoding='utf-8') as csvs:
            csvs_text = csvs.read()

        tree = parser.parse(csvs_text)
        schema = visitor.visit(tree)

        self.global_directives = schema.global_directives.directives
        self.column_rules = {str(col_def.name): col_def.rule for col_def in schema.body.column_defs}
        self.row_count = 0
        self.errors = {}  # TODO: Should be a defaultdict

    def validate(self, csv_file):
        valid = True

        quoting = csv.QUOTE_ALL if self.global_directives['quoted'] else csv.QUOTE_MINIMAL
        delimiter = self.global_directives['separator'] if self.global_directives['separator'] else ','

        with open(csv_file, newline='') as cf:
            # column count check
            first_line = cf.readline().split(delimiter)
            if len(first_line) != len(self.column_rules):
                # TODO: Raise some error
                pass

            # check column names
            if self.global_directives['no_header']:
                fieldnames = list(self.column_rules.keys())
            else:
                fieldnames = None

                first_line = cf.readline().split(delimiter)
                comparison = list(self.column_rules.keys())
                if self.global_directives['ignore_column_name_case']:
                    first_line = [header.lower() for header in first_line]
                    comparison = [header.lower() for header in comparison]

                if first_line != comparison:
                    # TODO: raise some error
                    pass

            # validate rows
            reader = csv.DictReader(cf,
                                    quoting=quoting,
                                    fieldnames=fieldnames,
                                    delimiter=delimiter)

            if self.global_directives['ignore_column_name_case']:
                temp_rules = self.column_rules
            else:
                temp_rules = {k.lower(): v for k, v in self.global_directives.items()}

            self.row_count = 0 if self.global_directives['no_header'] else 1

            for row in reader:
                self.row_count += 1
                for key in temp_rules.keys():
                    if not temp_rules[key].validate(row[key], row, self):
                        valid = False

            return valid











