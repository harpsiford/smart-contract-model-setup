import sys
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import accuracy_score
from sklearn.externals import joblib


def evaluate(model, X, y):
    y_pred = model.predict(X)

    total = len(X)
    accu = accuracy_score(y, y_pred)
    [p], [r], [f], [s] = precision_recall_fscore_support(y, y_pred, labels=[1])
    s /= total
    score = total, s, accu, p, r, f
    print('[EVAL]size %d, support %.3f, accuracy %.3f, precision %.3f, recall %.3f, fscore %.3f' % score)
    return score


if __name__ == '__main__':
    try:
        model_file = sys.argv[1]
        data_file = sys.argv[2]
    except KeyError:
        print('Usage: python3 evaluate_model.py model.pkl.z datafile.csv')
        exit(0)
    model = joblib.load(model_file)
    data = pd.read_csv(data_file)
    X_test = data['Opcodes']
    y_test = data['Vulnerable']
    total, support, accuracy, precision, recall, f1 = evaluate(model, X_test, y_test)

