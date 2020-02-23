# Spark initialization
import pyspark
from io import StringIO
from csv import reader


def init_KNN(file_name, sc , pool_size):

    data = sc.textFile(file_name).map(lambda x: list(reader(StringIO(x)))) \
                                 .map(lambda x: x[0])

    return data.takeSample(False, pool_size)

def distance(v1 , v2):

    '''
    Now only consider Euclidean distance
    '''
    dis = 0
    for i in range(len(v1)):

        if (v1[i].isnumeric()):
            dis += (float(v1[i]) - float(v2[i])) ** 2

    return dis

def KNN(KNN_pool, k, instance):

    vote_pool = []
    pool_size = len(KNN_pool)

    for i in range (pool_size):

        sim = distance(instance , KNN_pool[i])
        vote_pool.append((sim , KNN_pool[i][41]))

    #sort the vote pool on the distance
    vote_pool = sorted(vote_pool, key=lambda tup: tup[0])

    votes_for_normal = 0
    votes_for_anomaly = 0
    for i in range (k):
        if (vote_pool[i][1] == "normal") : votes_for_normal += 1
        else : votes_for_anomaly += 1
    if(votes_for_normal >= votes_for_anomaly) : return 0
    else : return 1
