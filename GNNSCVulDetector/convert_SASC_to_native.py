"""
Converts https://huggingface.co/datasets/mwritescode/slither-audited-smart-contracts/ to valid.json
(single-label, reentrancy)
"""
import re
import sys
import json
import uuid
import pandas as pd
from tools.reentrancy.AutoExtractGraph import generate_graph
from tools.reentrancy.graph2vec import elimination_node, embedding_node, embedding_edge, construct_vec


def flatten(A):
    rt = []
    for i in A:
        if isinstance(i, list): rt.extend(flatten(i))
        else: rt.append(str(i))
    return rt

def extract_node_features(source_code_lines: list):
    nodeNum = 0
    node_list = []
    node_attribute_list = []

    for line in source_code_lines:
        node = list(map(str, line.split()))
        verExist = False
        for i in range(0, len(node_list)):
            if node[1] == node_list[i]:
                verExist = True
            else:
                continue
        if verExist is False:
            node_list.append(node[1])
            nodeNum += 1
        node_attribute_list.append(node)

    return nodeNum, node_list, node_attribute_list


def elimination_edge(source_code_lines: list):
    # eliminate edge #
    edge_list = []  # all edge
    extra_edge_list = []  # eliminated edge

    for line in source_code_lines:
        edge = list(map(str, line.split()))
        edge_list.append(edge)

    # The ablation of multiple edge between two nodes, taking the edge with the edge_operation priority
    for k in range(0, len(edge_list)):
        if k + 1 < len(edge_list):
            start1 = edge_list[k][0]  # start node
            end1 = edge_list[k][1]  # end node
            op1 = edge_list[k][4]
            start2 = edge_list[k + 1][0]
            end2 = edge_list[k + 1][1]
            op2 = edge_list[k + 1][4]
            if start1 == start2 and end1 == end2:
                op1_index = dict_EdgeOpName[op1]
                op2_index = dict_EdgeOpName[op2]
                # extract edge attribute based on priority
                if op1_index < op2_index:
                    extra_edge_list.append(edge_list.pop(k))
                else:
                    extra_edge_list.append(edge_list.pop(k + 1))

    return edge_list, extra_edge_list

def remove_comments(source_code):
    # source: https://stackoverflow.com/questions/2319019/using-regex-to-remove-comments-from-source-files
    # comment by ishmael
    COMMENT_RE = re.compile(r"(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*$)", re.MULTILINE|re.DOTALL)
    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return "" # so we will return empty to remove the comment
        else: # otherwise, we will return the 1st group
            return match.group(1) # captured quoted-string
    return COMMENT_RE.sub(_replacer, source_code)


def extract_features(source_code):
    source_code = remove_comments(source_code)
    node_feature, edge_feature = generate_graph(source_code)
    node_feature = sorted(node_feature, key=lambda x: (x[0]))
    edge_feature = sorted(edge_feature, key=lambda x: (x[2], x[3]))
    node = [' '.join(flatten(fs)) for fs in node_feature]
    edge = [' '.join(flatten(fs)) for fs in edge_feature]

    nodeNum, node_list, node_attribute_list = extract_node_features(node)
    node_attribute_list, extra_var_list = elimination_node(node_attribute_list)
    node_encode, var_encode, node_embedding, var_embedding = embedding_node(node_attribute_list)

    edge_list, extra_edge_list = elimination_edge(edge)
    edge_encode, edge_embedding = embedding_edge(edge_list)
    node_vec, graph_edge = construct_vec(edge_list, node_embedding, var_embedding, edge_embedding, edge_encode)
    
    graph_data = dict(node_features=[n[1] for n in node_vec], graph=graph_edge, contract_name="???", targets="1 or 0")
    return graph_data


if __name__ == '__main__':
    contracts = pd.read_parquet(sys.argv[1], engine='fastparquet')
    print(f'Loaded {len(contracts.index)} contracts from {sys.argv[1]}')
    with open(sys.argv[2], 'a') as f:
        for i, contract in contracts.iterrows():
            # fields: 'contracts', 'source_code', 'bytecode', 'results'
            try:
                graph_data = extract_features(contract.source_code)
            except: 
                continue
            graph_data['contract_name'] = contract.contracts

            slither_results = json.loads(contract.results)['results'].get('detectors', [])
            slither_results = [d['check'] for d in slither_results]
            slither_result = 'reentrancy-no-eth' in slither_results or 'reentrancy-eth' in slither_results
            graph_data['targets'] = str(int(slither_result))
            f.write(json.dumps(graph_data, sort_keys=True) + ',\n')
