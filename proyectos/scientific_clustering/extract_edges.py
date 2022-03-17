#Adapter for the force_layout_map program

'''
 File: extract_edges.py
 Version: 1.1
 Date of modification: July of 2013
 Description: Extracts edges from a graph file to generate input file for the force layout map.
 See: force_layout_map.py
 *************************************
 Usage: python extract_edges.py [graph file]
 
 Input: A graph file with the format
          #time: x
          number of vertices (n)
          vertex  vertex1 num1 year indegree outdegree     ---> TODO: Get description for num1
          vertex  vertex2 num1 year indegree outdegree
          #seed                  ----> New in this version
          vertex  vertexi num1 year indegree outdegree       ----> Where vertexi is the seed of the cluster
          ...
          vertex vertexn  num1 year indegree outdegree
          edge   vertexi vertexj weight projction_size?
          edge   vertexx vertexy num1 num2
          
 Output: A text file with the seed and edges of the graph. Follows the format
         seed vertexi
         vertexi  vertexj  weight
'''

import sys
import os

cluster_file_name=sys.argv[1]
file_base_name=sys.argv[2]

weight_sum=0.0

FILE=open(file_base_name+".edges","w")

print 'reading file'
try:
    cluster_file=open(cluster_file_name,'r')
    rows=cluster_file.readlines()
    cluster_file.close()
except IOError:
    print 'file could not be opened'
    sys.exit(1)

ctime=rows[0]
n=int(rows[1])
m=len(rows)-n-3
print 'n: ',n,' m:',m

#Vamos a tener que barrer los nodos para saber cual es la semilla.
for i in range(2,n+2):
    new_line = rows[i].strip()
    try:
        line_array = new_line.split()
        if len(line_array)==2:
            seed_line=rows[i+1].strip()
            line_array = seed_line.split()
            (type, vertex_id, num1, num2, num3, num4)=line_array
            seed=vertex_id
            print 'SEED vertex:',vertex_id
            FILE.write("seed ")
            FILE.write(vertex_id)
            FILE.write("\n")
            break
    except ValueError:
        continue

#Tenemos que hacer una primer pasada al archivo para calcular el promedio de los pesos.
for i in range(n+3,len(rows)):
    new_line = rows[i].strip()
    try:
        line_array = new_line.split()
        (type, id1, id2, weight, num)=line_array
        weight_sum= weight_sum + float(weight)
    except ValueError:
        continue

weight_average= weight_sum/m
print weight_average

#Hacemos la segunda pasada para dividir peso entre peso promedio
for i in range(n+3,len(rows)):
    new_line = rows[i].strip()
    try:
        line_array = new_line.split()
        (type, id1, id2, weight, num)=line_array
        normalized_weight=float(weight)/weight_average
        #print id1,' ',id2,' ',normalized_weight
        FILE.write(id1)
        FILE.write(" ")
        FILE.write(id2)
        FILE.write(" ")
        FILE.write(str(normalized_weight))
        FILE.write("\n")
    except ValueError:
        continue

FILE.close()
