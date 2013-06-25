#!/bin/bash

fileList=( "$@" )

# Determine the last file in the list.  This is the output file.
#numberOfFiles=${#fileList[@]}
#lastPosition=$(($numberOfFiles - 1))
#outputFile=${fileList[${lastPosition}]}

# Remove the output file from the list of files, leaving just the input files.
#unset fileList[${#fileList[@]}-1]

# Check that a file with the name of the output file doesn't already exist.
#if [ -f $outputFile ]
#then
#  echo "ERROR:"
#  echo -e "\tA file with the name '$outputFile' already exists"
#  echo -e "\tThis is the name of the file to contain a list of filenames."
#  echo -e "\tThis file must not exist prior to running this task."
#  exit 0
#fi

for file in ${fileList[@]}
do
  echo $file
done
