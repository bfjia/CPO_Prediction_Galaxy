#!/bin/bash

head -1 ${1[1]} > combined.tsv

IFS=',' read -ra ADDR <<< "$1" #hax to read in a csv

head -1 ${ADDR[0]} > ./combined.tsv
for i in "${ADDR[@]}"; do
        echo $i
        tail -1 $i >> ./combined.tsv
done