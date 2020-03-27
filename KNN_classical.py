import pyspark
from io import StringIO
from csv import reader
import heapq


def vote(instance, train, k=100):
    votes = []
    for t in train:
        dist = distance(t, instance)
        heapq.heappush(votes, (dist, t))

    votes = heapq.nsmallest(k, votes)

    cnt_normal = 0
    cnt_anomaly = 0
    for v in votes:
        if v[-1][-1] == 'normal':
            cnt_normal += 1
        else:
            cnt_anomaly += 1

    if cnt_normal > cnt_anomaly:
        return 'normal'
    else:
        return 'anomaly'


def distance(x, y):
    dist = 0.0
    for i in range(len(x) - 1):
        if is_float(x[i]):
            dist += (float(x[i]) - float(y[i])) ** 2
        elif x[i] != y[i]:
            dist += 10000
    return dist


def is_float(v):
    try:
        float(v)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    conf = pyspark.SparkConf().setMaster("local[*]")
    sc = pyspark.SparkContext(appName="ClassicalKNN", conf=conf)

    data = sc.textFile('./input_dir/raw_data[0-5].csv').map(lambda x: list(reader(StringIO(x)))[0])
    test, train = data.randomSplit(weights=[0.8, 0.2])
    train = train.collect()

    pred_and_labels = test.map(lambda x: (vote(x, train, k=10), x[-1]))

    true_pos = pred_and_labels.filter \
        (lambda x: x[0] == x[1] and x[0] == 'anomaly') \
        .map(lambda x: ('True positive', 1)) \
        .reduceByKey(lambda x, y: x + y).collect()[0][1]
    false_pos = pred_and_labels \
        .filter(lambda x: x[0] != x[1] and x[0] == 'anomaly') \
        .map(lambda x: ('False positive', 1)) \
        .reduceByKey(lambda x, y: x + y).collect()[0][1]
    true_neg = pred_and_labels \
        .filter(lambda x: x[0] == x[1] and x[0] == 'normal') \
        .map(lambda x: ('True negative', 1)) \
        .reduceByKey(lambda x, y: x + y).collect()[0][1]
    false_neg = pred_and_labels \
        .filter(lambda x: x[0] != x[1] and x[0] == 'normal') \
        .map(lambda x: ('False negative', 1)) \
        .reduceByKey(lambda x, y: x + y).collect()[0][1]

    accuracy = (true_pos + true_neg) / (true_pos + true_neg + false_pos + false_neg)
    precision = true_pos / (true_pos + false_pos)
    recall = true_pos / (true_pos + false_neg)

    print("Accuracy: {:0.5f}".format(accuracy))
    print("Precision: {:0.5f}".format(precision))
    print("Recall: {:0.5f}".format(recall))
    print("F1 Measure: {:0.5f}".format((2 * precision * recall / (precision + recall))))