# Project Abstract

Real time network intrusion detection system is a system used to detect anomalous network activities based on streams of network traffic data. It is more flexible and scalable than signature-based intrusion detection system. In this project, we will simulate network traffic streams by replaying pre-captured network packets feature data at a certain rate. Micro-Cluster Nearest Neighbor (MC-NN) data stream classifier will be used to classify the packet as normal or anomalous traffic. The packet feature data set is labeled, and the detection result will be evaluated against the labels. In addition, MC-NN classifier will be implemented as it is not part of Spark official library. Also, comparative study will be performed between MC-NN and KNN.
