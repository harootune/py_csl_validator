# third party
from lark import Lark

# local
import py_csl_validator.visitors.csl_visitor_1_2 as cv


def find_version_number(schema_file_path):
    with open(schema_file_path, mode='r', newline='', encoding='utf-8') as csvs:
        version_line = ''
        while not version_line:
            version_line = csvs.readline().strip()

        version_line = version_line.split()

        if version_line[1] in ['1.0', '1.1', '1.2']:
            return version_line[1]
        else:
            # TODO: raise some error
            pass


def find_visitor(version):
    versions = {
        '1.0': cv.CslVisitor1_2,
        '1.1': cv.CslVisitor1_2,
        '1.2': cv.CslVisitor1_2,
    }

    return versions[version]


def find_parser(version):
    versions = {
        '1.0': 'csv_schema_1-2.lark',
        '1.1': 'csv_schema_1-2.lark',
        '1.2': 'csv_schema_1-2.lark',
    }

    current_version = versions[version]

    with open(f'py_csl_validator/grammars/{current_version}', mode='r', newline='', encoding='utf-8') as grammar_file:
        grammar_text = grammar_file.read()

    return Lark(grammar_text)
