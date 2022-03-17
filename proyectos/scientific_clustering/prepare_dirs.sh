#!/bin/sh

# prepare_dirs.sh
# 
#
# Created by Sara Garza on 7/30/13.
# Copyright 2013 UANL. All rights reserved.
#
# Description: Creates the necessary directories for generating tag clouds out of the extracted graph clusters.
# Usage: ./prepare_dirs [source directory]


SOURCE_DIRECTORY=$1
PREFIX=$2
RESULTS_DIRECTORY=$PREFIX"_"$(basename $SOURCE_DIRECTORY)

mkdir $RESULTS_DIRECTORY
mkdir $RESULTS_DIRECTORY/src
mkdir $RESULTS_DIRECTORY/clouds
mkdir $RESULTS_DIRECTORY/xml
mkdir $RESULTS_DIRECTORY/gradients

echo $RESULTS_DIRECTORY