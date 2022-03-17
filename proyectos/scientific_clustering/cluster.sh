#/bin/bash

for file in `ls -1 data/subcollections/*.proc`
do
    python cluster.py $file 
done
