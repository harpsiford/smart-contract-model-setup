import pandas as pd

# test-data.csv is created from vuls.csv and op.rm.stopwords.csv from the original repo
test_data = pd.read_csv('test-data.csv')
new_test_data = pd.DataFrame()

new_test_data['Addr'] = test_data['Addr']
new_test_data['Vulnerable'] = test_data['Reentrancy']
new_test_data['Opcodes'] = test_data['Opcodes']

new_test_data.to_csv('test-data-for-eval.csv', index=False)
