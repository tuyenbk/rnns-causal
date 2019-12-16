from __future__ import print_function

import sys
import math
import numpy as np
import pandas as pd

from keras import backend as K
from keras.models import Model
from keras.layers import LSTM, Input, Dense, Dropout
from keras.callbacks import ModelCheckpoint, CSVLogger, EarlyStopping
from keras import regularizers
from keras.optimizers import Adam

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range = (0, 1))

from functools import partial, update_wrapper

def wrapped_partial(func, *args, **kwargs):
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func

def weighted_mse(y_true, y_pred, weights):
    return K.mean(K.square(y_true - y_pred) * weights, axis=-1)

# Select gpu
import os
gpu = sys.argv[-10]
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"]= "{}".format(gpu)

from tensorflow.python.client import device_lib
print(device_lib.list_local_devices())

imp = sys.argv[-1]
T = sys.argv[-2] 
t0 = sys.argv[-3] 
dataname = sys.argv[-4] 
nb_batches = int(sys.argv[-5])
nb_epochs = int(sys.argv[-6])
lr = sys.argv[-7]
penalty = sys.argv[-8]
dr = sys.argv[-9]

def create_model(n_pre, nb_features, output_dim, lr, penalty, dr):
    """ 
        creates, compiles and returns a RNN model 
        @param nb_features: the number of features in the model
    """
    # Define model parameters

    n_hidden = 128

    inputs = Input(shape=(n_pre, nb_features), name="Inputs")
    weights_tensor = Input(shape=(n_pre, nb_features), name="Weights")
    lstm_1 = LSTM(n_hidden, dropout=dr)(inputs) 
    output= Dense(output_dim, kernel_regularizer=regularizers.l2(penalty), name='Dense')(lstm_1)

    cl = wrapped_partial(weighted_mse, weights=weights_tensor)

    model = Model([inputs, weights_tensor], output)

    model.compile(optimizer=Adam(lr=lr), loss=cl)

    print(model.summary()) 

    return model

def train_model(model, dataX, dataY, weights, nb_epoches, nb_batches):

    # Prepare model checkpoints and callbacks

    filepath="results/lstm/{}".format(dataname) + "/weights.{epoch:02d}-{val_loss:.3f}.hdf5"
    checkpointer = ModelCheckpoint(filepath=filepath, monitor='val_loss', verbose=1, period=5, save_best_only=True)

    stopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=50, verbose=0, mode='auto')

    csv_logger = CSVLogger('results/lstm/{}/training_log_{}_{}.csv'.format(dataname,dataname,imp), separator=',', append=False)

    history = model.fit(x=[dataX,weights], 
        y=dataY, 
        batch_size=nb_batches, 
        verbose=1,
        epochs=nb_epoches, 
        callbacks=[checkpointer,stopping,csv_logger],
        validation_split=0.1)

def test_model():

    n_pre =int(t0)-1
    seq_len = int(T)

    wx = np.array(pd.read_csv("data/{}-wx-{}.csv".format(dataname,imp)))  
    wx_scaled = scaler.fit_transform(wx)  

    print('raw wx shape', wx_scaled.shape)  

    wX = []
    for i in range(seq_len-n_pre):
        wX.append(wx_scaled[i:i+n_pre]) # controls are inputs
    
    wXC = np.array(wX)

    print('wXC shape:', wXC.shape)
    
    x = np.array(pd.read_csv("data/{}-x-{}.csv".format(dataname,imp)))
    x_scaled = scaler.fit_transform(x)

    print('raw x shape', x.shape)   

    dXC, dYC = [], []
    for i in range(seq_len-n_pre):
        dXC.append(x_scaled[i:i+n_pre]) # controls are inputs
        dYC.append(x_scaled[i+n_pre]) # controls are outputs
    
    dataXC = np.array(dXC)
    dataYC = np.array(dYC)

    print('dataXC shape:', dataXC.shape)
    print('dataYC shape:', dataYC.shape)

    nb_features = dataXC.shape[2]
    output_dim = dataYC.shape[1]

    # create and fit the lstm network
    print('creating model...')
    model = create_model(n_pre, nb_features, output_dim, lr, penalty, dr)
    train_model(model, dataXC, dataYC, wXC, int(nb_epochs), int(nb_batches))

    # now test

    print('Generate predictions on full training set')

    preds_train = model.predict([dataXC,wXC], batch_size=int(nb_batches), verbose=1)

    preds_train = scaler.inverse_transform(preds_train) # reverse scaled preds to actual values

    preds_train = np.squeeze(preds_train)

    print('predictions shape =', preds_train.shape)

    print('Saving to results/lstm/{}/lstm-{}-train-{}.csv'.format(dataname,dataname,imp))

    np.savetxt("results/lstm/{}/lstm-{}-train-{}.csv".format(dataname,dataname,imp), preds_train, delimiter=",")

    print('Generate predictions on test set')

    wy = np.array(pd.read_csv("data/{}-wy-{}.csv".format(dataname,imp)))

    wy_scaled = scaler.fit_transform(wy)    

    print('raw wy shape', wy_scaled.shape)  

    wY = []
    for i in range(seq_len-n_pre):
        wY.append(wy_scaled[i:i+n_pre]) # controls are inputs
    
    wXT = np.array(wY)

    print('wXT shape:', wXT.shape)

    y = np.array(pd.read_csv("data/{}-y-{}.csv".format(dataname,imp)))

    y_scaled = scaler.fit_transform(y)
     
    print('raw y shape', y_scaled.shape)   

    dXT = []
    for i in range(seq_len-n_pre):
        dXT.append(y_scaled[i:i+n_pre]) # treated is input

    dataXT = np.array(dXT)

    print('dataXT shape:', dataXT.shape)

    preds_test = model.predict([dataXT, wXT], batch_size=int(nb_batches), verbose=1)

    preds_test = scaler.inverse_transform(preds_test) # reverse scaled preds to actual values

    preds_test = np.squeeze(preds_test)

    print('predictions shape =', preds_test.shape)

    print('Saving to results/lstm/{}/lstm-{}-test-{}.csv'.format(dataname,dataname,imp))

    np.savetxt("results/lstm/{}/lstm-{}-test-{}.csv".format(dataname,dataname,imp), preds_test, delimiter=",")

def main():
    test_model()
    return 1

if __name__ == "__main__":
    main()