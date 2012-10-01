#!/bin/bash

filelist=$1

files=$(for file in $(cat $dir/$filelist); do echo $file; done)
firstfile=$(echo $files | cut -d " " -f1)
(
zcat $dir/$firstfile | head -1000 | grep "^#"
for file in $files
do
  zcat $dir/$file | grep -v "^#"
done
)
