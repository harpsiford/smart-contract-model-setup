import argparse
import pickle


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Smart Contracts Vulnerability Detection')
    parser.add_argument('-m', '--model-path', help='Path to the saved model checkpoint', type=str)
    parser.add_argument('-d', '--data-path', help='Path to labeled data for f1 evaluation', type=str)
    args = parser.parse_args()

    with open(args.model_path, 'rb') as f:
        model = pickle.load(f)

    # TODO: replace pattern1test, pattern2test, pattern3test, graph_test, y_test
    model.test()

