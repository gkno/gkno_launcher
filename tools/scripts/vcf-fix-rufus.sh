#!/bin/bash

IN=$1
OUT=$2
HEADER=$3

cp $HEADER $OUT
more $IN | grep -v '^#' | awk -v a='GT' -v b='0/1' -F $'\t' 'BEGIN {OFS = FS} {print $1,$2,$3,$4,$5,$6,$7,$8,a,b}' >> $OUT
