from lark import Lark

with open('./grammars/csv_schema_1-2.lark', mode='r', newline='', encoding='utf-8') as grammar_file:
    grammar_text = grammar_file.read()
    parser = Lark(grammar_text)

with open('test.csvs', mode='r', newline='', encoding='utf- 8') as csvs_file:
    csvs_text = csvs_file.read()

tree = parser.parse(csvs_text)
print(tree.pretty())
