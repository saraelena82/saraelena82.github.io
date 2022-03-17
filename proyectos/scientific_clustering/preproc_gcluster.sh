#!/bin/sh

#  preproc_gcluster.sh
#  
#
#  Created by Sara E. Garza on 7/30/13.
#
# Removes the lines "# time" and "# seed" from a given file and redirects this output to a new file.

FILENAME=$1
DESTINATION_DIR=$2
SOURCE_FILE_BNAME=$(basename $FILENAME) #Get base name for file

echo "Processing "$FILENAME
sed '1d' $FILENAME | sed s/'# seed'//g | grep -v ^$ > $DESTINATION_DIR/$SOURCE_FILE_BNAME
