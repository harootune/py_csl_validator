# third party
from lark import Lark

# local
from py_csl_validator.visitors.schema_validator import CslRuleset


with open('py_csl_validator/grammars/csv_schema_1-2.lark', mode='r', newline='', encoding='utf-8') as grammar_file:
    grammar_text = grammar_file.read()
    parser = Lark(grammar_text)

with open('test.csvs', mode='r', newline='', encoding='utf-8') as csvs_file:
    csvs_text = csvs_file.read()

tree = parser.parse(csvs_text)
print(tree.pretty())

ruleset = CslRuleset(tree)
print(ruleset.schema.body)
print(ruleset.schema.body.column_defs)
print(ruleset.schema.prolog.version)
