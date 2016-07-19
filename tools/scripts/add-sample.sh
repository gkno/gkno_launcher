#!/bin/bash

IN=$1
OUT=$2
SAMPLE=$3

cp $IN $OUT
echo '##INFO=<ID=CVT,Number=1,Type=String,Description="Unknown">' >> $OUT
echo '##INFO=<ID=VT,Number=A,Type=String,Description="Unknown">' >> $OUT
echo '##INFO=<ID=AO,Number=A,Type=Integer,Description="Unknown">' >> $OUT
echo '##INFO=<ID=HD,Number=A,Type=Integer,Description="Unknown">' >> $OUT
echo '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">' >> $OUT
echo '##contig=<ID=1>' >> $OUT
echo '##contig=<ID=2>' >> $OUT
echo '##contig=<ID=3>' >> $OUT
echo '##contig=<ID=4>' >> $OUT
echo '##contig=<ID=5>' >> $OUT
echo '##contig=<ID=6>' >> $OUT
echo '##contig=<ID=7>' >> $OUT
echo '##contig=<ID=8>' >> $OUT
echo '##contig=<ID=9>' >> $OUT
echo '##contig=<ID=10>' >> $OUT
echo '##contig=<ID=11>' >> $OUT
echo '##contig=<ID=12>' >> $OUT
echo '##contig=<ID=13>' >> $OUT
echo '##contig=<ID=14>' >> $OUT
echo '##contig=<ID=15>' >> $OUT
echo '##contig=<ID=16>' >> $OUT
echo '##contig=<ID=17>' >> $OUT
echo '##contig=<ID=18>' >> $OUT
echo '##contig=<ID=19>' >> $OUT
echo '##contig=<ID=20>' >> $OUT
echo '##contig=<ID=21>' >> $OUT
echo '##contig=<ID=22>' >> $OUT
echo '##contig=<ID=X>' >> $OUT
echo '##contig=<ID=Y>' >> $OUT
echo '##contig=<ID=hs37d5>' >> $OUT
echo -e '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t'$SAMPLE >> $OUT
