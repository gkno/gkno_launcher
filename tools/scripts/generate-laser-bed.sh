#!/bin/bash

input=$1
output=$2

awk '{if(NR>1){print $1, $2-1, $2, $3;}}' $input > $output
