library(ggplot2)

args <- commandArgs(TRUE)
inputFile <- args[1]
outputFile <- args[2]
percentage <- as.numeric(args[3])
title <- args[4]
xlabel <- args[5]
ylabel <- args[6]

hist <- read.table(inputFile, header = FALSE, check.names = FALSE, sep = " ")

cutoff <- max(hist$V2) * percentage
xmax <- max(which(hist$V2 > cutoff))
hist <- head(hist, xmax)

plot <- ggplot(data = hist) + 
geom_bar(aes(x = V1, y = V2), fill = 'skyblue', stat = "identity") +
xlim(0, xmax) +
scale_y_log10() +
theme_bw(12) + 
ggtitle(title) +
labs(x = xlabel, y = ylabel)

ggsave(filename = outputFile, height = 10, width = 10)
