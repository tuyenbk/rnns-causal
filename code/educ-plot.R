# Plot time-series and causal impacts

require(reshape2)
require(dplyr)
require(zoo)
require(matrixStats)
require(tseries)
require(ggplot2)
require(readr)

source(paste0(code.directory,"TsPlot.R"))
source(paste0(code.directory, "utils.R"))

capacity.outcomes <- readRDS("/media/jason/Dropbox/github/land-reform/data/capacity-outcomes.rds")

PlotEduc<- function(estimator,treated.indices,x,y.title,limits,breaks,t0,run.CI){
  ## Create time series data
  
  observed <- t(capacity.outcomes[[x]]$M)[,!colnames(t(capacity.outcomes[[x]]$M)) %in% c("TN")]
  observed.treated <- as.matrix(observed[,colnames(observed) %in% treated.indices][(t0+1):nrow(observed),])
  observed.control <- as.matrix(observed[,!colnames(observed) %in% treated.indices][(t0+1):nrow(observed),])
  
  pred.treated <- read_csv(paste0(results.directory, estimator,"/educ/",estimator,"-educ-test.csv"), col_names = FALSE)
  pred.control <- read_csv(paste0(results.directory, estimator,"/educ/",estimator,"-educ-train.csv"), col_names = FALSE)
  
  t.stat <- rowMeans(observed.treated - pred.treated) 
  
  if(run.CI){
    CI.treated <- PermutationCI(pred.control, 
                              observed.control, 
                              t.stat,
                              ncol(observed.control)-1, 
                              np=10000, 
                              l=500, 
                              prec=1e-03)
  
    saveRDS(CI.treated, paste0(results.directory, estimator,"/educ/",estimator,"-CI-treated.rds"))
  } else{
    CI.treated <- readRDS(paste0(results.directory, estimator,"/educ/",estimator,"-CI-treated.rds"))
  }
  
  ## Plot time series 
  
  treat.status <- matrix(colnames(observed), nrow=ncol(observed), ncol=1)
  treat.status[colnames(observed) %in% c(treated.indices)] <- "PLS"
  treat.status[!colnames(observed) %in% treated.indices] <- "SLS"
  treat.status <- matrix(treat.status, dimnames=list(NULL, "status"))
  
  observed.mean <-  aggregate(t(observed), list(treat.status), mean)[-1]
  predicted.mean <-  aggregate(rbind(t(pred.control),t(pred.treated)), list(treat.status), mean)[-1]
  pointwise.mean <- aggregate(rbind(t(observed.control),t(observed.treated))-rbind(t(pred.control),t(pred.treated)), 
                              list(treat.status), mean, na.rm=TRUE)[-1]
  
  ts.means <- cbind(t(observed.mean), rbind(matrix(NA, t0,2), t(predicted.mean)), rbind(matrix(NA, t0,2), t(pointwise.mean))) 
  colnames(ts.means) <- c("observed.pls","observed.sls","predicted.pls","predicted.sls","pointwise.pls","pointwise.sls")
  ts.means <- cbind(ts.means, "year"=as.numeric(rownames(ts.means)))
  ts.means.m <- melt(data.frame(ts.means), id.var=c("year"))
  
  CI.treated <- as.data.frame(CI.treated)
  CI.treated$year <- rownames(observed.treated)
  CI.treated$variable <- "pointwise.pls"
  colnames(CI.treated) <- c("upper","lower","year","variable")
  
  ts.means.m <- merge(ts.means.m, CI.treated, by=c("year","variable"), all.x=TRUE) # bind std. error

  # # Adjust year for plot
 # ts.means.m$year <- as.Date(as.yearmon(ts.means.m$year) + 11/12, frac = 1) # end of year
  ts.means.m$year <- as.Date(as.yearmon(ts.means.m$year)) 
  
  ts.means.m$year <- as.POSIXct(ts.means.m$year, tz="UTC")
  
  # Labels
  
  ts.means.m$series <- NA
  ts.means.m$series[grep("observed.", ts.means.m$variable)] <- "Time-series"
  ts.means.m$series[grep("predicted.", ts.means.m$variable)] <- "Time-series"
  ts.means.m$series[grep("pointwise.", ts.means.m$variable)] <- "Per-period impact"

  ts.means.m$series<- factor(ts.means.m$series, levels=c("Time-series", "Per-period impact")) # reverse order
  
  ts.plot <- TsPlot(df=ts.means.m,y.title=y.title,limits=limits, breaks=breaks)
  
  return(ts.plot)
}

treated.indices <- c("CA", "CO", "IA", "KS", "MI", "MN", "MO", "NE", "OH", "OR", "SD", "WA", "WI", "IL", "NV", "ID", "MT", "ND",  "UT", "AL", "MS", "AR", "FL", "LA", "IN", "NM", "WY", "AZ", "OK", "AK")

educ.ed <- PlotEduc(estimator="encoder-decoder",treated.indices,x='educ.pc',y.title="Log per-capita state government education spending (1942$)\n",limits=c(as.POSIXct("1809-01-01 01:00:00"), as.POSIXct("1942-01-01 01:00:00")), breaks=seq(as.POSIXct("1809-1-31 00:00:00",tz="UTC"),
                                                                                                                                             as.POSIXct("1942-1-31 00:00:00",tz="UTC"), "20 years"), t0=which(colnames(capacity.outcomes[["educ.pc"]]$M)=="1869"), run.CI=FALSE)

educ.rvae <- PlotEduc(estimator="rvae",treated.indices,x='educ.pc',y.title="Log per-capita state government education spending (1942$)\n",limits=c(as.POSIXct("1809-01-01 01:00:00"), as.POSIXct("1942-01-01 01:00:00")), breaks=seq(as.POSIXct("1809-1-31 00:00:00",tz="UTC"),
                                                                                                                                                                                                            as.POSIXct("1942-1-31 00:00:00",tz="UTC"), "20 years"), t0=which(colnames(capacity.outcomes[["educ.pc"]]$M)=="1869"), run.CI=FALSE) 

ggsave(paste0(results.directory,"plots/educ-ed.png"), educ.ed, width=8.5, height=11)
ggsave(paste0(results.directory,"plots/educ-rvae.png"), educ.rvae, width=8.5, height=11)