#!/bin/bash

INSERT=$1
shift
DIR=$@
NAME_COUNTER=1

# Loop over all BAM files in the directory.
for BAM in ${DIR}
do
  NAME=`echo "$NAME" | cut -d '.' -f 1`
  if [[ $name == '' ]]
  then
    NAME='name_'$NAME_COUNTER
    NAME_COUNTER=$(($NAME_COUNTER + 1))
  fi
  echo $BAM $INSERT $NAME
done
