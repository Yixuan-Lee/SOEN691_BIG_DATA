from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from io import StringIO
from csv import reader

import KNN as real_time_KNN

def RT_KNN(sc , pool):

    ssc = StreamingContext(sc, 1)   #Streaming will execute in each 3 seconds
    #lines = ssc.textFileStream("hdfs://localhost:9000/input_dir")

    lines = ssc.textFileStream("./input_dir").map(lambda x: list(reader(StringIO(x))))\
                                             .map(lambda x: x[0])


    test = lines.map(lambda  x : (real_time_KNN.KNN(pool , 10, x) , x[41]))\
                .map(lambda x: ("Correct" , 1) if x[0] == x[1] else ("Error" , 1))\

    test.pprint()

    ssc.start()
    ssc.awaitTermination()

if __name__ == "__main__":

    sc = SparkContext(appName="PysparkStreaming")
    KNN_pool = real_time_KNN.init_KNN('./source_dir/Train.csv', sc, 100)
    RT_KNN(sc , KNN_pool)
