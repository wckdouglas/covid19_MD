#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "[usage] bash $0 <data file name>"
    exit
fi

DATA_NAME=$1 #./data/2020-09-24.tsv

cat $DATA_NAME | grep Ca | sed "s/ - /$(echo '\t')/g"  | sed 's/,//g' > a
mv a $DATA_NAME
echo Written $DATA_NAME
