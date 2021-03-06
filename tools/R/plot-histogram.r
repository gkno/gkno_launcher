library(reshape2)
library(ggplot2)

args <- commandArgs(TRUE)
hist<-read.table(args[1], header=TRUE, check.names=FALSE)
hist.melted <- melt(hist, id = "bin")

min <- 0
max <- 0
for (i in names(hist)[-1]) {
  hist2  <- rep(hist[,1], hist[,i])  ## expands the data by frequency of #score
  median <- median(hist2)
  quant  <- quantile(hist2, c(0.90))
  
  # Handle missing values
  if (is.na(median)) { median <- 0 }
  if (is.na(quant)) { quant <- 0 }

  # Update the min and max.
  if ( (median + quant) > max) {max <- (median + quant)}
  if ( (median - quant) < min) {min <- (median - quant)}
}                                               
                                                
if (min < 0) {min <- 0}
                    
pdf(args[2])

# Use user defined values for the min and max x-values if provided.
if (as.integer(args[6]) != -1) {min <- as.integer(args[6])}
if (as.integer(args[7]) != -1) {max <- as.integer(args[7])}

if (exists(args[8])) {
  if (args[8] == "log") {log = TRUE}
  else {log = FALSE}
} else {
  log = FALSE
}
if (log == TRUE) {
  ggplot() + geom_line(data=hist.melted, aes(x=bin, y=value, group=variable, colour=variable)) + xlim(min, max) + xlab(args[3]) + ylab(args[4]) + theme_bw(12) + scale_colour_discrete(name=args[5]) + scale_y_log10()
} else {
  ggplot() + geom_line(data=hist.melted, aes(x=bin, y=value, group=variable, colour=variable)) + xlim(min, max) + xlab(args[3]) + ylab(args[4]) + theme_bw(12) + scale_colour_discrete(name=args[5])
}
