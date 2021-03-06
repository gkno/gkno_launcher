library(reshape2)
library(ggplot2)

hist<-read.table("hist.txt", header=TRUE)
hist.melted <- melt(hist, id = "bin")

min <- 0
max <- 0
for (i in names(hist)[-1]) {
  hist2 <- rep(hist[,1], hist[,i])  ## expands the data by frequency of #score
  median <- median(hist2)
  quant <- quantile(hist2, c(0.90))

  # Update the min and max.
  if ( (median + quant) > max) {max <- (median + quant)}
  if ( (median - quant) < min) {min <- (median - quant)}
}                                               
                                                
if (min < 0) {min <- 0}
                    
ggplot() + geom_line(data=hist.melted, aes(x=bin, y=value, group=variable, colour=variable)) + xlim(min, max)
