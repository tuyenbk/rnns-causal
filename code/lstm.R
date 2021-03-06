###################################
# LSTM for Simulations #
###################################

library(keras)
library(reticulate)
library(readr)
# use_python("/usr/local/bin/python")
use_python("~/venv/bin/python") # comet

lstm <- function(Y,treat_indices,d, t0, T){
  # Converting the data to a floating point matrix
  data <- data.matrix(t(Y)) # T x N

  # Splits
  train_data <- data[,(-treat_indices)] # train on control units

  test_data <- data[,(treat_indices)] # treated units

  write.csv(train_data,paste0("data/",d,"-x.csv"),row.names = FALSE)
  write.csv(test_data,paste0("data/",d,"-y.csv"),row.names = FALSE)
  
  py <- import_main()
  py$dataname <- d
  py$t0 <- t0
  py$T <- T
  py$gpu <- 3
  py$epochs <- 5000
  py$patience <- 100
  py$lr <- 0.001
  py$dr <- 0.5
  py$penalty <- 0.2
  if(d %in% c("educ","covid")){
    py$penalty <- 0.5
  }
  if(d %in% c("stock")){
    py$nb_batches <- 32
  }
  if(d %in% c("educ","covid")){
    py$nb_batches <- 16
  }else{
    py$nb_batches <- 8
  }
  
  source_python("code/train_lstm_sim.py")
  
  lstm.pred.test <- as.matrix(read_csv(paste0("results/lstm/",d,"/lstm-",d,"-test.csv"), col_names = FALSE))
  
  return(t(lstm.pred.test))  # N x T
}
