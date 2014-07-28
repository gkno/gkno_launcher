# Get required libraries
library(reshape2)
library(ggplot2)

# Import data
parent1 <- read.table("parent1.r.histo", header=FALSE)
parent2 <- read.table("parent2.r.histo", header=FALSE)
child   <- read.table("child.r.histo", header=FALSE)

# Calculate the coverage of all three samples.
temp <- which(diff(sign(diff(parent1$V2)))==-2)+1
parent1Coverage <- temp[2] - 1

temp <- which(diff(sign(diff(parent2$V2)))==-2)+1
parent2Coverage <- temp[2] - 1

temp <- which(diff(sign(diff(child$V2)))==-2)+1
childCoverage <- temp[2] - 1

# Store the max coverage of all the samples.
maxCoverage <- max(parent1Coverage, parent2Coverage, childCoverage)

# Determine the number of k-mers at the coverage peak and identify the max.
parent1Count <- parent1$V2[parent1Coverage]
parent2Count <- parent2$V2[parent2Coverage]
childCount   <- child$V2[childCoverage]
maxCount     <- max(parent1Count, parent2Count, childCount)

# Set up the 'data' data frame to hold all data
data <- parent1

# Rename the columns and add the parent2 and child data
names(data)  <- c("Coverage", "Parent1")
data$Parent2 <- parent2$V2
data$Child   <- child$V2

# Melt the data into long format
data.melt <- melt(data, id.vars = 'Coverage', variable.name = 'Sample', value.name = 'Count')

# Plot the data
ggplot(data.melt, aes(x = Coverage, y = Count, color = Sample)) +
geom_line() +
scale_color_manual(values = c('Parent1' = 'skyblue', 'Parent2' = 'skyblue4', 'Child' = 'indianred')) +
xlim(0, 1.5 * maxCoverage) + 
ylim(0, 1.02 * maxCount)
