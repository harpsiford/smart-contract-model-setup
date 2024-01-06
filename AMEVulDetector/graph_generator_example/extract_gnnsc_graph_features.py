import numpy as np
from collections import defaultdict
from GraphGenerator import generate_graph, generate_potential_fallback_node
from Graph2Vec import elimination_node, embedding_node, embedding_edge, construct_vec


GNNSC_CONFIG = dict(
    NUM_EDGE_TYPES = 0,
    PARAMS = {  
        # BasicModel from GNNSC repo
        'num_epochs': 250,
        'patience': 200,
        'learning_rate': 0.002,
        'clamp_gradient_norm': 0.9,  # [0.8, 1.0]
        'out_layer_dropout_keep_prob': 0.9,  # [0.8, 1.0]

        'hidden_size': 256,  # 256/512/1024/2048
        'use_graph': True,

        'tie_fwd_bkwd': False,  # True or False
        'task_ids': [0],
    

        # GNNSCModel
        'num_nodes': 100000,
        'use_edge_bias': False,  # False or True

        'propagation_rounds': 2,
        'propagation_substeps': 20,  # [15, 20]

        'graph_rnn_cell': 'gru',  # gru or rnn
        'graph_rnn_activation': 'relu',  # tanh or relu
        'graph_state_dropout_keep_prob': 0.9,  # [0.5, 1.0]

        'task_sample_ratios': {}
    }
)


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


def __tensorise_edge_sequence(edges, NUM_EDGE_TYPES):
    sending_nodes = []  # type: List[List[np.ndarray]]
    msg_targets = []  # type: List[List[np.ndarray]]
    receiving_nodes = []  # type: List[np.ndarray]
    all_nodes = set()
    for step_edges in edges:
        msg_targets_uniq = set(w for (_, __, w) in step_edges)
        recv_nodes = list(sorted(msg_targets_uniq))
        recv_nodes_to_uniq_id = {v: i for (i, v) in enumerate(recv_nodes)}

        sending_nodes_in_step = []
        msg_targets_in_step = []
        for target_e_typ in range(NUM_EDGE_TYPES):
            sending_nodes_in_step.append(
                np.array([v for (v, e_typ, _) in step_edges if e_typ == target_e_typ], dtype=np.int32))
            msg_targets_in_step.append(
                np.array([recv_nodes_to_uniq_id[w] for (_, e_typ, w) in step_edges if e_typ == target_e_typ],
                            dtype=np.int32))
        msg_targets.append(msg_targets_in_step)
        sending_nodes.append(sending_nodes_in_step)
        receiving_nodes.append(np.array(recv_nodes, dtype=np.int32))
        all_nodes.update(v for (v, _, __) in step_edges)
        all_nodes.update(w for (_, __, w) in step_edges)

    all_updated_nodes = set()
    all_updated_nodes.update(v for step_receiving_nodes in receiving_nodes
                                for v in step_receiving_nodes)
    initial_nodes = list(sorted(all_nodes - all_updated_nodes))

    return np.array(initial_nodes, dtype=np.int32), sending_nodes, msg_targets, receiving_nodes


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


def __graph_to_propagation_schedules(graph, config):
        num_incoming_edges = defaultdict(lambda: 0)
        outgoing_edges = defaultdict(lambda: [])
        # Compute number of incoming edge per nodes, and build adjacency lists:
        for (v, typ, w) in graph:
            num_incoming_edges[v] += 1  # zy: why edge are added on both sides??
            num_incoming_edges[w] += 1
            edge_bwd_typ = typ if config['PARAMS']['tie_fwd_bkwd'] else config['NUM_EDGE_TYPES'] + typ  # zy: what's this for
            outgoing_edges[v].append((v, typ, w))
            outgoing_edges[w].append((w, edge_bwd_typ, v))

        # Sort them, pick nodes with lowest number of incoming edge:
        tensorised_prop_schedules = []
        for prop_round in range(int(config['PARAMS'][
                                        'propagation_rounds'])):  # propagation_rounds=1 #for prop_round in range(int(config['PARAMS']['propagation_rounds'] / 2)):
            dag_seed = min(num_incoming_edges.items(), key=lambda t: t[1])[prop_round]
            node_depths = {}

            # bfs_visit(outgoing_edges, node_depths, dag_seed, 0)

            for _, deepvalue in enumerate(num_incoming_edges):
                node_depths[deepvalue] = deepvalue

            # Now split edge into forward/backward sets, by using their depths.
            # Intuitively, a nodes with depth h will get updated in step h.
            max_depth = max(node_depths.values())
            assert (max_depth <= config['PARAMS']['propagation_substeps'])
            fwd_pass_edges = [[] for _ in range(max_depth)]
            bwd_pass_edges = [[] for _ in range(max_depth)]
            for (v, typ, w) in graph:
                edge_bwd_type = typ if config['PARAMS']['tie_fwd_bkwd'] else config['NUM_EDGE_TYPES'] + typ
                v_depth = node_depths[v]
                w_depth = node_depths[w]
                if v_depth < w_depth:  # "Forward": We are going up in depth:
                    fwd_pass_edges[w_depth - 1].append((v, typ, w))
                    bwd_pass_edges[-v_depth - 1].append((w, edge_bwd_type, v))
                elif w_depth < v_depth:  # "Backward": We are going down in depth
                    fwd_pass_edges[v_depth - 1].append((w, edge_bwd_type, v))
                    bwd_pass_edges[-w_depth - 1].append((v, typ, w))
                else:
                    # ignore self loops:
                    assert v == w

            tensorised_prop_schedules.append(__tensorise_edge_sequence(fwd_pass_edges, config['NUM_EDGE_TYPES']))
            tensorised_prop_schedules.append(__tensorise_edge_sequence(bwd_pass_edges, config['NUM_EDGE_TYPES']))

        return tensorised_prop_schedules


from typing import Sequence, Any
def process_raw_graphs(raw_data: Sequence[Any], config):  #, is_training_data: bool) -> Any:
        processed_graphs = []
        count = 0
        for d in raw_data:
            count += 1
            db = []
            # print("count: ", count)

            for nf in d["node_features"]:
                db.append(nf)

            prop_schedules = __graph_to_propagation_schedules(d['graph'], config)
            processed_graphs.append({
                "init": d["node_features"],
                'contract_n': d['contract_name'],
                "prop_schedules": prop_schedules,
                "target_values": [d["targets"][task_id][0] for task_id in config['PARAMS']['task_ids']]
            })

        is_training_data=False
        if is_training_data:
            pass
            #     # np.random.shuffle(processed_graphs)
            #     for task_id in config['PARAMS']['task_ids']:
            #         task_sample_ratio = config['PARAMS']['task_sample_ratios'].get(str(task_id))
            #         if task_sample_ratio is not None:
            #             ex_to_sample = int(len(processed_graphs) * task_sample_ratio)
            #             for ex_id in range(ex_to_sample, len(processed_graphs)):
            #                 processed_graphs[ex_id]['target_values'][task_id] = None

        return processed_graphs, count


def gnnsc_features(graph_dict, config):
    num_fwd_edge_types = max(0, max([e[1] for e in graph_dict['graph']]))
    config['NUM_EDGE_TYPES'] = max(config['NUM_EDGE_TYPES'], num_fwd_edge_types * (1 if config['PARAMS']['tie_fwd_bkwd'] else 2))
    return process_raw_graphs([graph_dict], config)  #, is_training_data)




if __name__ == "__main__":
    """
    Unfortunately, the additonal processing step is useless for generating features in valid.txt.
    """
    test_contract = "../data_example/reentrancy/source_code/simple_dao.sol"
    node_feature, edge_feature = generate_graph(test_contract)
    node_feature = sorted(node_feature, key=lambda x: (x[0]))
    edge_feature = sorted(edge_feature, key=lambda x: (x[2], x[3]))
    # node_feature, edge_feature = generate_potential_fallback_node(node_feature, edge_feature)
    
    node = [' '.join(flatten(fs)) for fs in node_feature]
    edge = [' '.join(flatten(fs)) for fs in edge_feature]
    print("node_feature:\n", '\n'.join(node))
    print("edge_feature:\n", '\n'.join(edge))
    nodeNum, node_list, node_attribute_list = extract_node_features(node)
    node_attribute_list, extra_var_list = elimination_node(node_attribute_list)
    node_encode, var_encode, node_embedding, var_embedding = embedding_node(node_attribute_list)
    edge_list, extra_edge_list = elimination_edge(edge)
    edge_encode, edge_embedding = embedding_edge(edge_list)
    node_vec, graph_edge = construct_vec(edge_list, node_embedding, var_embedding, edge_embedding, edge_encode)

    # graph_data = 
    graph_dict = dict(node_features=[n[1] for n in node_vec], graph=graph_edge, contract_name="???", targets="1")
    encoded_graph_features, num_graph = gnnsc_features(graph_dict, GNNSC_CONFIG)
    print('encoded_graph_features:\n', encoded_graph_features)
    import pdb; pdb.set_trace()

