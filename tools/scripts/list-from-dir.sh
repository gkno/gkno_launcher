#!/bin/bash

DIR=$1
EXTENSION=$2

for FILE in $DIR/*
do
  FILE_EXT=`echo "$FILE" | rev | cut -d '.' -f 1 | rev`
  if [ $FILE_EXT == $EXTENSION ]
  then
    echo $FILE
  fi
done
