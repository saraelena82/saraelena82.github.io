#!/bin/sh

#  genaugraphs.sh
#  
#
#  Created by Sara E. Garza on 8/10/13.
#

SOURCE_DIRECTORY=$1
PREFIX=$2
RESULTS_DIRECTORY=`./prepare_author_dirs.sh $SOURCE_DIRECTORY $PREFIX`

echo "===CREATING ERROR LOG FILE==="
touch au_error.log

for file in `ls $SOURCE_DIRECTORY`
do
 echo $file
./vis_author.sh $SOURCE_DIRECTORY $file $RESULTS_DIRECTORY
done