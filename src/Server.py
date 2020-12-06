import tensorflow as tf2
import tensorflow.compat.v1 as tf
tf.disable_eager_execution()
from tqdm import tqdm

from Client import Clients

def buildClients(num):
    learning_rate = 0.0001
    # num_input = 28  # image shape: 28*28
    # num_input_channel = 1  # image channel: 3
    num_input = 32
    num_input_channel = 3
    # num_classes = 10  # Cifar-10 total classes (0-9 digits)
    num_classes = 100
    # num_classes = 10    # mnist total classes (0-9)

    #create Client and model
    return Clients(input_shape=[None, num_input, num_input, num_input_channel],
                  num_classes=num_classes,
                  learning_rate=learning_rate,
                  clients_num=num)


def run_global_test(client, global_vars, test_num):
    client.set_global_vars(global_vars)
    acc, loss = client.run_test(test_num)
    print("[epoch {}, {} inst] Testing ACC: {:.4f}, Loss: {:.4f}".format(
        ep + 1, test_num, acc, loss))


#### SOME TRAINING PARAMS ####
CLIENT_NUMBER = 100
CLIENT_RATIO_PER_ROUND = 0.12
# epoch = 360
epoch = 6   # during debugging

#### CREATE CLIENT AND LOAD DATASET ####
client = buildClients(CLIENT_NUMBER)

loss = []

#### BEGIN TRAINING ####
global_vars = client.get_client_vars()
# 假定在第 6 轮的时候对第 6 个参与者进行成员推理攻击
for ep in range(epoch):
    # We are going to sum up active clients' vars at each epoch
    client_vars_sum = None

    # Choose some clients that will train on this epoch
    random_clients = client.choose_clients(CLIENT_RATIO_PER_ROUND)

    # Train with these clients
    for client_id in tqdm(random_clients, ascii=True):
        # Restore global vars to client's model
        client.set_global_vars(global_vars)

        # train one client
        prediction, modelY, loss = client.train_epoch(cid=client_id)

        # obtain current client's vars
        current_client_vars = client.get_client_vars()
        # loss = client.loss
        # print(loss, type(loss))

        # sum it up
        if client_vars_sum is None:
            client_vars_sum = current_client_vars
        else:
            for cv, ccv in zip(client_vars_sum, current_client_vars):
                cv += ccv
    # obtain the avg vars as global vars
    global_vars = []
    for var in client_vars_sum:
        global_vars.append(var / len(random_clients))

    # run test on 1000 instances
    run_global_test(client, global_vars, test_num=600)


#### FINAL TEST ####
run_global_test(client, global_vars, test_num=1000)
