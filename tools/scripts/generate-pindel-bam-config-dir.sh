#!/bin/bash

DIR=$1
INSERT=$2

# Remove trailing slash if present.
DIR=${DIR%/}

# Use absolute path.
DIR=$(realpath $DIR)

# Check that the directory contains bam files.
ls -1 $DIR/*.bam > /dev/null 2> /dev/null
if [ $? != 0 ]
then
  echo 'No BAM file'
  exit 1
fi

# Loop over all BAM files in the directory.
for BAM in `ls -1 $DIR/*.bam`
do
  NAME=${BAM#$DIR/}
  NAME=`echo "$NAME" | cut -d '.' -f 1`
  echo $BAM $INSERT $NAME
done
