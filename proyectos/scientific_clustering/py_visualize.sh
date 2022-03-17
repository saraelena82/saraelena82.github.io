#!/bin/sh

#  py_visualize.sh
#  
#
#  Created by Sara E. Garza on 5/16/13.
#

CLUSTER_PATH=$1 #Path for the cluster text file (subgraph)
RESULTS_PATH=$2  #Path where visualization is to be stored

#Get the name of the file only (without the whole path and without the extension)
FILENAME=`./strip_extension.sh $CLUSTER_PATH` #Strip suffix

#Prepare file for Python force layout program
python extract_edges.py $CLUSTER_PATH $FILENAME

#Run the graph visualization tool (produces a file called 'coordinates.dat', which is later renamed with the source file's name)
python force_layout_map.py $FILENAME.edges
mv coordinates.dat $FILENAME.dat
mv cluster.eps $FILENAME.eps

#Move all generated files to the indicated path (places the .dat and the .fig into a subfolder called 'src', which should exist)
mv $FILENAME.edges $RESULTS_PATH/edges/
mv $FILENAME.dat $RESULTS_PATH/coordinates/
mv $FILENAME.eps $RESULTS_PATH/eps/