# Get required libraries
library(reshape2)
library(ggplot2)

# Import data
args   <- commandArgs(TRUE)
mother <- read.table(args[1], header=FALSE)
father <- read.table(args[2], header=FALSE)
child  <- read.table(args[3], header=FALSE)

# Calculate the coverage of all three samples.
temp <- which(diff(sign(diff(mother$V2)))==-2)+1
motherCoverage <- temp[2] - 1

temp <- which(diff(sign(diff(father$V2)))==-2)+1
fatherCoverage <- temp[2] - 1

temp <- which(diff(sign(diff(child$V2)))==-2)+1
childCoverage <- temp[2] - 1

# Store the max coverage of all the samples.
maxCoverage <- max(motherCoverage, fatherCoverage, childCoverage)

# Determine the number of k-mers at the coverage peak and identify the max.
motherCount <- mother$V2[motherCoverage]
fatherCount <- father$V2[fatherCoverage]
childCount  <- child$V2[childCoverage]
maxCount    <- max(motherCount, fatherCount, childCount)

# Set up the 'data' data frame to hold all data
data <- mother

# Rename the columns and add the parent2 and child data
names(data) <- c("coverage", "mother")
data$father <- father$V2
data$child  <- child$V2

# Melt the data into long format
data.melt <- melt(data, id.vars = 'coverage', variable.name = 'sample', value.name = 'count')

# Plot the data
pdf(args[4])
ggplot(data.melt, aes(x = coverage, y = count, color = sample)) + geom_line() + scale_color_manual(values = c('mother' = 'skyblue', 'father' = 'skyblue4', 'child' = 'indianred')) + xlim(0, 1.5 * maxCoverage) + ylim(0, 1.02 * maxCount) + theme_bw(12)
