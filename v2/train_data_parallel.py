import numpy as np

import threading

class ParamServer:
    def __init__(self, model, learning_rate, momentum_coeff, losses):
        self.model = model
        self.learning_rate = learning_rate
        self.momentum_coeff = momentum_coeff
        self.losses = losses
        self.lock = threading.Lock()

    def update_gradients(self, loss, linear_out, conv_out):
        with self.lock:
            self.losses.append(loss)
            self.model.update(self.learning_rate, self.momentum_coeff, linear_out, conv_out)

class ParamWorker:
    def __init__(self, model, param_server, data, labels):
        self.model = model
        self.param_server = param_server
        self.data = data
        self.labels = labels

    def compute_gradients(self):
        (curr_loss, _, relu_x_mult, linear_input, softmax, new_labels, maxpool_input_shape, maxpool_grad_mask) = self.model.forward(self.data, self.labels)
        linear_out, conv_out = self.model.backward(self.data, relu_x_mult, linear_input, softmax, new_labels, maxpool_input_shape, maxpool_grad_mask)
        return curr_loss, linear_out, conv_out

    def run(self):
        curr_loss, linear_out, conv_out = self.compute_gradients()
        self.param_server.update_gradients(curr_loss, linear_out, conv_out)
    


def train_epoch_data_parallel(model, batch_size, learning_rate, momentum_coeff, trainX, trainY, pureTrainY, testX, testY, pureTestY):
    num_images = np.shape(trainX)[0]
    num_test = np.shape(testX)[0]
    permut = np.random.choice(num_images, num_images, replace=False)
    trainX = trainX[permut]
    trainY = trainY[permut]
    pureTrainY = pureTrainY[permut]
    num_batches = int(np.ceil(num_images/batch_size))
    losses = []
    third_batch = int(batch_size/3)
    third_images = int(num_images/3)
    
    param_server = ParamServer(model, learning_rate, momentum_coeff, losses)
    param_workers = []
    for i in range(num_batches):
        start = i*third_batch
        end = (i+1)*third_batch
        currX = np.concatenate([trainX[start:end], trainX[start + third_images:end + third_images], trainX[start + 2*third_images:end + 2*third_images]])
        currY = np.concatenate([trainY[start:end], trainY[start + third_images:end + third_images], trainY[start + 2*third_images:end + 2*third_images]])
        curr_worker = ParamWorker(model, param_server, currX, currY)
        param_workers.append(curr_worker)
    
    threads = []
    for worker in param_workers:
        thread = threading.Thread(target=worker.run)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
        
    train_loss = np.sum(losses)/num_images
    
    _, train_pred, _, _, _, _, _, _ = model.forward(trainX, trainY)
    train_accu = np.count_nonzero(train_pred == pureTrainY)/num_images
    test_loss, test_pred, _, _, _, _, _, _ = model.forward(testX, testY)
    test_loss = test_loss/num_test
    test_accu = np.count_nonzero(test_pred == pureTestY)/num_test
    return train_loss, train_accu, test_loss, test_accu