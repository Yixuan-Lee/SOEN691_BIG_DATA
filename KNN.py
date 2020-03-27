
from io import StringIO
from csv import reader
from collections import deque
from typing import Deque


def init_KNN(file_name, sc, pool_size):
    # create an RDD
    data = sc.textFile(file_name).map(lambda x: list(reader(StringIO(x)))[0])

    # return a pool_size sample subset of an RDD as pool
    return deque(data.takeSample(False, pool_size), maxlen=pool_size)


def distance(v1, v2):
    '''
    Now only consider Euclidean distance
    '''
    dis = 0
    for i in range(len(v1)):
        if v1[i].isnumeric():
            dis += (float(v1[i]) - float(v2[i])) ** 2
    return dis

max_size = 300



def KNN(KNN_pool:Deque, k, instance):
    vote_pool = []

    for i in KNN_pool:
        sim = distance(instance, i)
        vote_pool.append((sim, i[-1]))

    # update pool
    KNN_pool.popleft()
    KNN_pool.append(instance)


    # sort the vote pool on the distance
    vote_pool = sorted(vote_pool, key=lambda tup: tup[0])

    votes_for_normal = 0
    votes_for_anomaly = 0
    for i in range(k):
        if vote_pool[i][1] == "normal":
            votes_for_normal += 1
        else:
            votes_for_anomaly += 1
    if votes_for_normal >= votes_for_anomaly:
        return "normal"
    else:
        return "anomaly"

