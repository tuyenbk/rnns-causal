from __future__ import print_function

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sys
import math
import numpy as np
import pandas as pd

from keras import backend as K
from keras.utils.vis_utils import plot_model, model_to_dot
from keras.models import Model
from keras.layers import LSTM, Input, Dropout
from keras.callbacks import ModelCheckpoint, CSVLogger
from keras import regularizers
from keras.optimizers import Adam, SGD

# Select gpu
import os
gpu = sys.argv[-4]
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"]= "{}".format(gpu)

from tensorflow.python.client import device_lib
print(device_lib.list_local_devices())

analysis = sys.argv[-1] # 'treated' or 'control'
dataname = sys.argv[-2] # 'votediff' 'sim'

BATCHES = 8

if dataname == 'california':
    BATCHES = 4

if dataname == 'germany':
    BATCHES = 4

if dataname == 'votediff':
    BATCHES = 3

def create_model(n_pre, n_post, nb_features, output_dim):
    """ 
        creates, compiles and returns a RNN model 
        @param n_pre: the number of previous time steps (input)
        @param n_post: the number of posterior time steps (output or predictions)
        @param nb_features: the number of features in the model
        @param output_dim: the dimension of the target sequence
    """
    # Define model parameters
    
    initialization = 'glorot_normal'
    activation = 'linear'
    lr = 0.0005
    penalty=0.1
    dr=0.5

    if analysis == 'control': 
        dr=0.5
        penalty=0.1
        lr = 0.001

    if analysis == 'treated-gans': 
        dr=0.5
        penalty=0.001
        lr = 0.001

    inputs = Input(shape=(n_pre, nb_features,), name="Inputs")
    dropout_1 = Dropout(dr)(inputs)
    lstm_1 = LSTM(output_dim, activation=activation, kernel_regularizer=regularizers.l2(penalty), kernel_initializer=initialization, return_sequences=False)(dropout_1) 

    model = Model(inputs=inputs, output=lstm_1)

    model.compile(loss="mean_squared_error", optimizer=Adam(lr=lr)) 

    if dataname == 'votediff':
        lr = 0.00001
        model.compile(loss="mean_squared_error", optimizer=Adam(lr=lr))

    return model

def test_sinus():
    ''' 
        testing how well the network can predict
        a simple sinus wave.
    '''
    # Load saved data
    if dataname == 'votediff':
        n_post  = 1 
        n_pre =  47-1
        seq_len = 52   
        
    if dataname == 'basque':
        n_post  = 1 
        n_pre =  14-1 
        seq_len = 43
    
    if dataname == 'california':
        n_post  = 1 
        n_pre =  19-1 
        seq_len = 31

    if dataname == 'germany':
        n_post  = 1 
        n_pre =  30-1 
        seq_len = 44  
        
    if dataname == 'west-revpc':
        n_post  = 1 
        n_pre =  52-1 
        seq_len = 119  

    if dataname == 'west-exppc':
        n_post  = 1 
        n_pre =  51-1 
        seq_len = 117  

    if dataname == 'west-educpc':
        n_post  = 1 
        n_pre =  37-1 
        seq_len = 99  

    if dataname == 'south-revpc':
        n_post  = 1 
        n_pre =  36-1 
        seq_len = 97  

    if dataname == 'south-exppc':
        n_post  = 1 
        n_pre =  37-1 
        seq_len = 98  

    if dataname == 'south-educpc':
        n_post  = 1 
        n_pre =  33-1 
        seq_len = 90 
    y = np.array(pd.read_csv("data/{}-y.csv".format(dataname)))
    x = np.array(pd.read_csv("data/{}-x.csv".format(dataname)))    

    if analysis == 'treated-rnns': 
        print('raw x shape', x.shape)   

        print('raw y shape', y.shape)   

        dX, dY = [], []
        for i in range(seq_len-n_pre-n_post):
            dX.append(x[i:i+n_pre]) # controls are inputs
            # dY.append(y[i+n_pre:i+n_pre+n_post]) # treated is output
            dY.append(y[i+n_pre])

    if analysis == 'treated-gans': 
        print('raw x shape', x.shape)   

        print('raw y shape', y.shape)   

        dX, dY = [], []
        for i in range(seq_len-n_pre-n_post):
            dX.append(y[i:i+n_pre]) # treated is input
            # dY.append(y[i+n_pre:i+n_pre+n_post]) # treated is output
            dY.append(y[i+n_pre])

    if analysis == 'control': 

        print('raw x shape', x.shape)   

        dX, dY = [], []
        for i in range(seq_len-n_pre-n_post):
            dX.append(x[i:i+n_pre]) # controls are inputs
            # dY.append(x[i+n_pre:i+n_pre+n_post]) # controls are outputs
            dY.append(x[i+n_pre])
    
    dataX = np.array(dX)
    dataY = np.array(dY)

    print('dataX shape:', dataX.shape)
    print('dataY shape:', dataY.shape)

    nb_features = dataX.shape[2]
    output_dim = dataY.shape[1]

    # create and fit the LSTM network
    model = create_model(n_pre, n_post, nb_features, output_dim)
    # Load weights
    filename = sys.argv[-3]
    model.load_weights(filename, by_name=True)

    print("Created model and loaded weights from file")
    
    # now test

    print('Generate predictions')

    predict = model.predict(dataX, batch_size=BATCHES, verbose=1)

    predict = np.squeeze(predict)

    print('predictions shape =', predict.shape)

    np.savetxt("{}-{}-test.csv".format(filename,dataname), predict, delimiter=",")

def main():
    test_sinus()
    return 1

if __name__ == "__main__":
    sys.exit(main())