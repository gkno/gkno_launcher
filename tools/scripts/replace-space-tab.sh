#!/bin/bash

perl -n -e 's/ /\t/;print' $1
