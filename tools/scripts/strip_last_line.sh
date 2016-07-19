#!/bin/bash

IN=$1
OUT=$2

sed '$d' < $IN > $OUT
