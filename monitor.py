import pyspark
from pyspark.streaming import StreamingContext
from io import StringIO
from csv import reader

from KNN import Knn

def get_results(predictions_labels):
    # 4 conditions
    #     normal:   positive
    #     abnormal: negative
    true_pos = predictions_labels \
        .filter(lambda x: x[0] == x[1] and x[0] == 'normal') \
        .map(lambda x: ('True positive', 1)) \
        .reduceByKey(lambda x, y: x + y)
    false_pos = predictions_labels \
        .filter(lambda x: x[0] != x[1] and x[0] == 'normal') \
        .map(lambda x: ('False positive', 1)) \
        .reduceByKey(lambda x, y: x + y)
    true_neg = predictions_labels \
        .filter(lambda x: x[0] == x[1] and x[0] == 'anomaly') \
        .map(lambda x: ('True negative', 1)) \
        .reduceByKey(lambda x, y: x + y)
    false_neg = predictions_labels \
        .filter(lambda x: x[0] != x[1] and x[0] == 'anomaly') \
        .map(lambda x: ('False negative', 1)) \
        .reduceByKey(lambda x, y: x + y)

    if true_pos.count() == 0:
        true_pos = sc.parallelize(('true positive', 0))
    if false_pos.count() == 0:
        false_pos = sc.parallelize(('false positive', 0))
    if true_neg.count() == 0:
        true_neg = sc.parallelize(('true negative', 0))
    if false_neg.count() == 0:
        false_neg = sc.parallelize(('false negative', 0))

    return true_pos.union(false_pos.union(true_neg.union(false_neg)))

def saveCoord(rdd):

    rdd.foreach(lambda rec: open("myoutput.txt", "a").write(rec[0] + ":" +rec[1] + '\n'))

def updatePool(rdd):

    rdd.foreach(lambda rec: k1.simple_update_pool(rec))

def RT_KNN(sc):

    ssc = StreamingContext(sc, 1)  # Streaming will execute in each 3 seconds
    # read on Hadoop
    # lines = ssc.textFileStream("hdfs://localhost:9000/input_dir")

    lines = ssc.textFileStream("./input_dir").map(lambda x:
        list(reader(StringIO(x)))[0])

    # make predictions
    predictions_labels = lines.map(
        lambda x: (k1.KNN(10,x), x[-1]))

    predictions_labels.foreachRDD(saveCoord)
    predictions_labels.pprint()

    lines.foreachRDD(updatePool)

    # start StreamingContext
    ssc.start()
    ssc.awaitTermination()


if __name__ == "__main__":

    # spark initialization
    conf = pyspark.SparkConf().setMaster("local[2]")
    sc = pyspark.SparkContext(appName="PysparkStreaming", conf=conf)
    global k1

    k1 = Knn('./source_dir/Train.csv', sc, 500)
    RT_KNN(sc)