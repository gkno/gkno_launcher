library(cluster) 

# Get arguments from the command line.
args       <- commandArgs(TRUE)
refFile    <- args[1]
sampleFile <- args[2]
outputFile <- args[3]
clusters   <- as.integer(args[4])

# Get the reference and sample datasets.
refData    <- read.table(args[1], header = TRUE, colClasses = c(rep("character", 2), rep("real", 8), rep("NULL", 92)))
sampleData <- read.table(args[2], colClasses = c(rep("character", 2), rep("NULL", 3), rep("real", 8)), header = TRUE)

# Merge the reference and sample data frames.
completeData <- rbind(refData, sampleData)

p12 <- subset(completeData, select = c(PC1, PC2))
p13 <- subset(completeData, select = c(PC1, PC3))
p14 <- subset(completeData, select = c(PC1, PC4))
p23 <- subset(completeData, select = c(PC2, PC3))

# K-Means Cluster Analysis
fit12 <- kmeans(p12, clusters)
fit13 <- kmeans(p13, clusters)
fit14 <- kmeans(p14, clusters)
fit23 <- kmeans(p23, clusters)

# Get the populations with which the sample clusters.
data12 <- completeData
data12$kmeans <- fit12$cluster
pop12 <- unique(head((subset(data12, kmeans == tail(data12, n = 1)$kmeans))[1], -1))

data13 <- completeData
data13$kmeans <- fit13$cluster
pop13 <- unique(head((subset(data13, kmeans == tail(data13, n = 1)$kmeans))[1], -1))

data14 <- completeData
data14$kmeans <- fit14$cluster
pop14 <- unique(head((subset(data14, kmeans == tail(data14, n = 1)$kmeans))[1], -1))

data23 <- completeData
data23$kmeans <- fit23$cluster
pop23 <- unique(head((subset(data23, kmeans == tail(data23, n = 1)$kmeans))[1], -1))

# Get the list of all populations with which the sample clusters when considering
# plots of PC1 v PC2, PC1 v PC3, PC1 v PV4 and PC2 v PC3.
x <- unique(rbind(pop12, pop13, pop14, pop23))
write.table(x, file = outputFile, append = FALSE, quote = FALSE, sep = " ", 
                 eol = "\n", na = "NA", dec = ".", row.names = FALSE, 
                 col.names = FALSE, qmethod = c("escape", "double"))
