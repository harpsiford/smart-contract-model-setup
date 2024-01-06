import re
import os
import torch
import numpy as np
from MLP_layer import MLP


def split_function(source_code):
    function_list = []
    flag = -1

    for line in source_code.split('\n'):
        text = line.strip()
        if len(text) > 0 and text != "\n":
            if text.split()[0] == "function" or text.split()[0] == "constructor":
                function_list.append([text])
                flag += 1
            elif len(function_list) > 0 and ("function" or "constructor" in function_list[flag][0]):
                function_list[flag].append(text)
    return function_list


def extract_pattern(source_code):
    allFunctionList = split_function(source_code)  # Store all functions
    callValueList = []  # Store all functions that call call.value
    # otherFunctionList = []  # Store functions other than the functions that contains call.value
    pattern_list = [0, 0, 0]
    # Store functions other than W functions (with .call.value)
    for fn_lines in allFunctionList:
        flag = 0
        for line in fn_lines: 
            if '.call.value' in line:
                callValueList.append(fn_lines)
                flag += 1
        # if flag == 0:
            # otherFunctionList.append(allFunctionList[i])

    ################   pattern 1  #######################
    if len(callValueList) == 0:
        return pattern_list
    else:
        pattern_list[0] = 1

    ################   pattern 2  #######################
    for fn_lines in callValueList:
        CallValueFlag1 = 0

        for line in fn_lines:
            if '.call.value' in line:
                CallValueFlag1 += 1
            elif CallValueFlag1 != 0:
                line = line.replace(" ", "")
                if "-" in line or "-=" in line or "=0" in line:
                    pattern_list[1] = 1
                    break

    ################   pattern 3  #######################
    for fn_lines in callValueList:
        CallValueFlag2 = 0
        param = None

        for text in fn_lines:
            if '.call.value' in text:
                CallValueFlag2 += 1
                param = re.findall(r".call.value\((.+?)\)", text)[0]
            elif CallValueFlag2 != 0:
                if param in text:
                    pattern_list[2] = 1
                    break

    return pattern_list


def extract_feature_with_fc(pattern1, pattern2, pattern3):
    pattern1 = torch.Tensor(pattern1)
    pattern2 = torch.Tensor(pattern2)
    pattern3 = torch.Tensor(pattern3)
    model = MLP(4, 100, 250)

    pattern1FC = model(pattern1).detach().numpy().tolist()
    pattern2FC = model(pattern2).detach().numpy().tolist()
    pattern3FC = model(pattern3).detach().numpy().tolist()
    pattern_final = np.array([pattern1FC, pattern2FC, pattern3FC])
    # np.savetxt(outputPathFC, pattern_final, fmt="%.6f")

    return pattern_final


if __name__ == '__main__':
    inputFileDir = "../data_example/reentrancy/source_code/"

    for file in os.listdir(inputFileDir):
        with open(inputFileDir + file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        pattern_list = extract_pattern(source_code)
        assert len(pattern_list) == 3, f"Expected 3 patterns, received {len(pattern_list)}!"
        label = all(pattern_list)
    
    pattern1 = np.array([1, 0, 0, pattern_list[0]])
    pattern2 = np.array([0, 1, 0, pattern_list[1]])
    pattern3 = np.array([0, 0, 1, pattern_list[2]])
    
    pattern_fnn = extract_feature_with_fc(pattern1, pattern2, pattern3)
    print(pattern_fnn)

    pattern1 = np.array(np.pad(pattern1, (0, 246), 'constant'))
    pattern2 = np.array(np.pad(pattern2, (0, 246), 'constant'))
    pattern3 = np.array(np.pad(pattern3, (0, 246), 'constant'))

    pattern_zeropadding = np.array([pattern1, pattern2, pattern3])
    print(pattern_zeropadding)

    # import pdb; pdb.set_trace()
