#local
from  py_csl_validator.validator.validator import CslValidator

validator = CslValidator('test_2.csvs')

print(validator.schema)
print(validator.schema.ruleset.body)
