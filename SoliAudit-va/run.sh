#!/bin/bash

### Train
./vul-predict/main.py train -u run-anlyzers/vuls.csv.xz -o features/op.rm.stopwords.csv.xz -t Reentrancy -a logistic

### Test
evaluate_model.py ./vul-predict/.model/logistic/Reentrancy.pkl.z ./vul-predict/test-data-for-eval.csv
## obtaining test-data-for-eval.csv:
# from native dataset (test-data.csv appears only after training the model):
./vul-predict/convert_test_data_for_eval.py ./vul-predict/test-data.csv ./vul-predict/test-data-for-eval.csv 
# from SASC
./vul-predict/convert_SASC_to_opcodes.py ./SASC.csv ./vul-predict/test-data-for-eval.csv 
