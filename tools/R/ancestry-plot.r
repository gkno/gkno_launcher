library(ggplot2)

args <- commandArgs(TRUE)
referenceFile <- args[1]
sampleFile <- args[2]
outputFile <- args[3]
title <- args[4]
xlabel <- args[5]
ylabel <- args[6]

ref <- read.table(referenceFile, header = TRUE, check.names = FALSE)
sample <- read.table(sampleFile, header = TRUE, check.names = FALSE)

plot <- ggplot() + 
geom_point(data = ref, aes(x = PC1, y = PC2, colour = popID), shape = 1) + 
geom_point(data = sample, aes(x = PC1, y = PC2), shape = 18, size = 4) +
scale_colour_discrete(name = "Population") + 
theme_bw(12) + 
ggtitle(title) +
labs(x = xlabel, y = ylabel)

ggsave(filename = outputFile, height = 10, width = 10)
