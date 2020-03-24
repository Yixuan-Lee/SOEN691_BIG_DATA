import os
import random
import csv
import shutil
import numpy as np
from io import StringIO
from os.path import join
from csv import reader
from mcnnmc import MC

'''
改动的地方:
1. 每个mc文件头的信息：
    1) epsilon  : error counter
    2) n        : number of instances
    3) centroid : centroid
    4) CF2_x    : sum of the squares of the attributes in CF1_x
2. 每个rdd需要读：epsilon, n, centroid, CF2_x
    1) 先根据 centroid, n 算出 CF1_x
    2) 在根据 CF1_x, CF2_x 算出 vairiance
    3) 根据 centroid 算距离
    4) 不需要存每个点的数据
    5) Split : 找到最大的 variance 中的下标，先更新 CF1_x, 再根据 CF1_x 算出两个新的 
               centroid 写回去
    5) 如果用 foreachRDD，需要存下来:
          epsilon
          n 
          centroid (CF1_x / n)
          CF2_x
    6) 需要在 MCNN/predict 方法里把 (prediction, label, time) 写到一个新的文件
    7) 最后等所有 (prediction, label, time) 都存下来后，再写另一个py文件做 evaluation
'''


mc_folder = './mcnn_mcs'

# helper function
def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

# helper function
def clean_mc_folder():
    for filename in os.listdir(mc_folder):
        file_path = join(mc_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


class MC_NN:

    def __init__(self, theta):
        self.theta = theta
        self.pool = []  # a list of MC objects

        self.read_mcnn_pool()

    def read_mcnn_pool(self):
        '''
        read all centroid files into a self.pool
        :return:
        '''
        mc_files = [f for f in os.listdir('mcnn_mcs') if f.endswith('.csv')]

        for file in mc_files:
            mc = MC(self.theta)
            if file.__contains__('normal'):
                mc.cl = 'normal'
            elif file.__contains__('anomaly'):
                mc.cl = 'anomaly'

            with open(join(mc_folder, file), 'r') as f:
                lines = f.read().splitlines()

                mc.epsilon = int(lines[0])
                mc.n = int(lines[1])
                mc.centroid = [float(x) for x in lines[2].split(',')]
                # mc.cf2_x = [float(x) for x in lines[3].split(',')]

                # the following elements are instances in the mc
            #     mc.cf_all = [[x for x in line.split(',')] for line in lines[1:]]

            self.pool.append(mc)

    def euclidean_distance(self, v1, v2):
        distance = 0
        for i in range(len(v1)):
            distance += (v1[i] - v2[i]) ** 2
        return distance

    def find_true_nearest_mc(self, instance):
        true_label = instance[-1]
        features = [float(attr) for attr in instance if is_number(attr)]

        min_distance = float('inf')
        min_true_mc = None
        for mc in self.pool:
            if mc.cl == true_label:
                distance = self.euclidean_distance(features, mc.centroid)
                if distance < min_distance:
                    min_distance = distance
                    min_true_mc = mc
        return min_true_mc

    def predict_and_update_mcs(self, instance, true_label):
        # predict
        features = np.array([float(attr) for attr in instance if is_number(attr)])

        min_distance = float('inf')
        min_mc = None
        for mc in self.pool:
            distance = self.euclidean_distance(features, mc.centroid)
            if distance < min_distance:
                min_distance = distance
                min_mc = mc

        prediction = min_mc.cl

        # update micro clusters and save on disk
        if min_mc.cl == true_label:
            # scenario 1:
            # min_mc.cf_all.append(instance)

            min_mc.n += 1
            min_mc.centroid = (np.add(np.array(min_mc.centroid) * (min_mc.n - 1), features) / min_mc.n).tolist()

            if min_mc.epsilon > 0:
                min_mc.epsilon -= 1
        else:
            # scenario 2:
            # true_mc.cf_all.append(instance)

            true_mc = self.find_true_nearest_mc(instance)

            true_mc.n += 1
            true_mc.centroid = (np.add(np.array(true_mc.centroid) * (true_mc.n - 1), features) / true_mc.n).tolist()

            true_mc.epsilon += 1
            min_mc.epsilon += 1

            # TODO: check and split
            # ...

        # write updated mcs onto disk
        for mc in self.pool:
            if mc.cl == 'normal':
                with open(join(mc_folder, 'normal_mc_1.csv'), 'w', newline='') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow([mc.epsilon])
                    csv_writer.writerow([mc.n])
                    csv_writer.writerow(mc.centroid)
            elif mc.cl == 'anomaly':
                with open(join(mc_folder, 'anomaly_mc_1.csv'), 'w', newline='') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow([mc.epsilon])
                    csv_writer.writerow([mc.n])
                    csv_writer.writerow(mc.centroid)

        return prediction


def init_mcnn_pool(data_file, sc):
    '''
    initialize the pool with 1 normal instance and 1 anomaly instance,
    write 2 instances to 2 files

    :param data_file: dataset
    :param folder: save folder
    :param sc:
    :return:
    '''
    # read the data
    data = sc.textFile(data_file).map(lambda x: list(reader(StringIO(x)))[0])

    normal = None
    anomaly = None
    while normal is None or anomaly is None:
        rand = data.takeSample(withReplacement=False, num=1, seed=random.randint(0, 100))[0]

        if rand[-1] == 'normal' and normal is None:
            normal = rand
        elif rand[-1] == 'anomaly' and anomaly is None:
            anomaly = rand

    normal = [x for x in normal if is_number(x)]
    anomaly = [x for x in anomaly if is_number(x)]

    with open(join(mc_folder, 'normal_mc_1.csv'), 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow("0")  # initial epsilon
        csv_writer.writerow("1")  # initial count of instances in the cluster
        csv_writer.writerow(normal)
    with open(join(mc_folder, 'anomaly_mc_1.csv'), 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow("0")  # initial epsilon
        csv_writer.writerow("1")  # initial count of instances in the cluster
        csv_writer.writerow(anomaly)


def predict(instance):
    mcnn = MC_NN(theta=20)

    prediction = mcnn.predict_and_update_mcs(instance, instance[-1])

    # TODO: after the previous RDD deletes the files, the next RDD may fail to
    #       read the mc files.
    # clean_mc_folder()

    return None
