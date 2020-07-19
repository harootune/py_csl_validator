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

        self.schema = visitor(tree)
