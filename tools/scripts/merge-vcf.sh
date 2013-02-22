#!/bin/bash

filelist=$1

files=$(for file in $(cat $filelist); do echo $file; done)
firstfile=$(echo $files | cut -d " " -f1)
(
zcat $firstfile | head -1000 | grep "^#"
for file in $files
do
  zcat $file | grep -v "^#"
done
)
