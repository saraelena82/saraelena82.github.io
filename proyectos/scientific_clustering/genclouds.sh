#!/bin/sh

#  genclouds.sh
#  
#
#  Created by Sara E. Garza on 7/30/13.
#
# Description: Prepares results directory and runs tag cloud visualization for a group of graph clusters.

SOURCE_DIRECTORY=$1
PREFIX=$2
LOWER=$3
UPPER=$4
RESULTS_DIRECTORY=`./prepare_dirs.sh $SOURCE_DIRECTORY $PREFIX`

./vis_all_topics.sh $SOURCE_DIRECTORY $LOWER $UPPER $RESULTS_DIRECTORY
