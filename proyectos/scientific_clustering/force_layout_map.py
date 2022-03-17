#
# bioinformatics 3, wintersemester 89
# all code by Mathias Bader
#

########################
#TODO: Documentacion ###
# Esta clase es para generar la visualizacion de los subgrafos correspondientes a los clusters.
#
# Usage: python force_layout_map.py [edge file]
#   Edge file content:
#      node_id  other_node_id  weight
#      weights above 1.0 generate attractive forces, whereas weights below 1.0 (0.9, 0.5, etc.) generate repulsive forces
########################

import sys, os, string, random, time
from math import sqrt
# gives tk namespace for graphical output
import Tkinter as tk 

#filename = 'dog.dat'
#filename = 'stern.dat'
#filename = 'stern2.dat'
#filename = 'viereck.dat'
filename = 'dna.dat'
#filename = 'many_cc.dat'
#filename = '2287.dat'

center_distance = 10.0			# the distance from the middle of the screen to each border
scaling_factor = 1.0			# the zoom-factor (the smaller, the more surface is shown)
zooming = 0						# is the application zooming right now?
zoom_in_border = 1.0			# limit between graph and screen-border for zooming in
zooming_out = 0
circle_diameter = 20			# the diameter of the node-circles
timestep = 0
thermal_energie = 0.0			# set this to 0.3 or 0.0 to (de)activate thermal_energie
all_energies = []				# list of all energies sorted by time
highest_energy = 0				# the highest energie occuring
#energie_change_limit = 0.0000001	# if energie doesn't change more than this, process is stoped
energie_change_limit = 0.0001
velocity_maximum = 0.05
friction = 0.0005				# is subtracted from the velocity at each timestep for stop oscillations
show_energies_in_background = 0 #No queremos que se vea ningun mensaje...
status_message = ''
grabed_node = ''
grabed_component = ''
##dont_finish_calculating = 1
dont_finish_calculating = 0 ##Al parecer un 1 en este rubro hace que el proceso nunca termine
show_energie_in_background = 0 #No queremos que se vea ningun mensaje...
show_textinformation_in_background = 0 #Esto es para que se muestren los mensajes en el fondo...

##Tratamos de introducir los pesos
edge_weights={}

#screen properties
c_width = 1000
c_height = 600
border = 0 #Esto ayuda en algo? El original era 20...


if (len(sys.argv) == 2 and sys.argv[1] != ""):
	filename = sys.argv[1]


# Class for Nodes
class Node:
	def __init__(self, node_id):
		self.id = node_id		# id (as an integer for example)
		self.neighbour_ids = []	# list of the ids of the neighbours
		self.degree = 0			# number of neighbours
		self.coordinate_x = 0
		self.coordinate_y = 0
		self.force_coulomb = 0
		self.force_harmonic = 0
		self.cc_number = 0 		# the number of the connected component (0 if not assigned yet)
		self.cc_centers = []
		self.velocity = [0,0]	# instead of replacing the nodes, change its velocity to produce inertia
		self.movable = 1
		self.num_id=-1 #VAMOS A ASIGNAR UN "AUTO-NUMERO", INDEPENDIENTEMENTE DE LA ETIQUETA (id) DEL NODO
		self.isSeed=False
	def getNeighbours(self):
		return self.neighbour_ids
	def getDegree(self):
		return self.degree
	def getId(self):
		return self.id
	def setNeighbour(self, node_id):
		self.neighbour_ids.append(node_id)
		self.degree += 1
	def deleteNeighbour(self, node_id):
		self.neighbour_ids.remove(node_id)
		self.degree -= 1
	def setNumId(self, num_id):
                self.num_id=num_id
	def enableAsSeed(self): #Aqui definimos que el vertice es el semilla
		self.isSeed=True

# Class for graph
class Graph:
	def __init__(self):
		# build an empty graph
		self.nodes = [] # list of Node-objects
		self.edges = [] # list of tupels (node1-id, node2-id) where node1-id is always smaller than node2-id, in the weighted version this is a triple
		self.last_added_id = -1
		self.connected_components_count = 0
		self.overall_energie = 0
		self.overall_energie_difference = 1000
		self.calculation_finished = 0
		self.node_count=0
	
	def addNode(self, node_id):
		# adds a node to the graph
		if node_id == self.last_added_id: return	# speed up adding of same ids consecutively
		for x in self.nodes:
			if x.getId() == node_id:
				return
		new_node=Node(node_id)
		new_node.setNumId(self.node_count)
		#print "Setting this node ",new_node.id," # ",new_node.num_id
                self.nodes.append(new_node)
		self.last_added_id = node_id
		self.node_count=self.node_count + 1 #ESTO ES PARA SABER EL ID NUMERICO ACTUAL
	
	def addEdge(self, node_id_1, node_id_2, weight):
		# adds an edge between two nodes
		if node_id_1 != node_id_2 and node_id_1 >= 0 and node_id_2 >= 0 and not self.isEdge(node_id_1, node_id_2):
			if node_id_1 < node_id_2:
				self.edges.append((node_id_1, node_id_2))
			else:
				self.edges.append((node_id_2, node_id_1))
			# search for the two node-objects with fitting ids
			node1 = self.getNode(node_id_1)
			node2 = self.getNode(node_id_2)
			node1.setNeighbour(node_id_2)
			node2.setNeighbour(node_id_1)
			key=node_id_1,"_",node_id_2
			edge_weights[key]=weight
	
	def deleteEdge(self, (node_id_1, node_id_2)):
		# deletes the edge between node_id_1 and node_id_2
		if node_id_1 > node_id_2:
			# switch the two node-ids (edges are always saved with smaller id first)
			tmp = node_id_1
			node_id_1 = node_id_2
			node_id_2 = tmp
		self.edges.remove((node_id_1, node_id_2))
		node1 = self.getNode(node_id_1)
		node1.deleteNeighbour(node_id_2)
		node2 = self.getNode(node_id_2)
		node2.deleteNeighbour(node_id_1)
	
	def nodesList(self):
		# returns the list of ids of nodes
		list_of_ids = []
		for node in self.nodes:
			list_of_ids.append(node.id)
		return list_of_ids
	
	def edgesList(self):
		# returns the list of edges ([(id, id), (id, id), ...]
		return self.edges
	
	def degreeList(self):
		# returns a dictionary with the degree distribution of the graph
		degrees = {}
		for x in self.nodes:
			if degrees.has_key(x.degree):
				degrees[x.degree] += 1
			else:
				degrees[x.degree] = 1
		return degrees

        def getNodeCount(self):
                return self.node_count
	
	def countNodes(self):
		# prints the number of nodes
		return len(self.nodes)
	
	def countEdges(self):
		# prints the number of edges
		return len(self.edges)
	
	def printNodes(self):
		# prints the list of nodes
		to_print = '['
		count = 0
		for x in self.nodes:
			to_print = to_print + str(x.getId()) + ','
			count += 1
			if count > 200:
				print to_print, 
				to_print = ''
				count = 1
		if count > 0: to_print = to_print[:-1]
		to_print = to_print + ']'
		print to_print
	
	def printEdges(self):
		# prints the list of edges
		to_print = '['
		count = 0
		for (n1, n2) in self.edges:
			key=n1,"_",n2
			if key in edge_weights:
				eweight=edge_weights[n1,"_",n2]
			else:
				eweight=edge_weights[n2,"_",n1]
			to_print = to_print + '(' + str(n1) + ',' + str(n2) + ',' + str(eweight) + '), '
			count += 1
			if count > 200:
				print to_print, 
				to_print = ''
				count = 1
		if count > 0: to_print = to_print[:-2]
		to_print = to_print + ']'
		print to_print
	
	def printData(self):
		# prints number of nodes and edges
		filename="coordinates.dat"
		FILE=open(filename,"w")
		print 'graph with', len(self.nodes), 'nodes and', len(self.edges), 'edges'
		print
		for node in self.nodes:
			#print 'x coordinate of', node.id, 'is', node.coordinate_x
			#print 'y coordinate of', node.id, 'is', node.coordinate_y
			print node.id,'(',node.num_id,'),',node.coordinate_x,',', node.coordinate_y
			print
			FILE.write(str(node.id))
			FILE.write(" ")
			FILE.write(str(node.coordinate_x))
			FILE.write(" ")
			FILE.write(str(node.coordinate_y))
			FILE.write("\n")
		FILE.close()
		c.quit()
        #EL FORMATO DE ESTE ARCHIVO SE ADAPTA AL FORMATO QUE OCUPA EL PROGRAMA EN C QUE GENERA EL XFIG
        def printGraphData(self):
		# prints number of nodes and edges
		filename="coordinates.dat"
		FILE=open(filename,"w")
		print 'graph with', len(self.nodes), 'nodes and', len(self.edges), 'edges'
		print
		FILE.write("p edge n ")
		FILE.write(str(len(self.nodes)))
		FILE.write(" m ")
		FILE.write(str(len(self.edges)))
		FILE.write("\n")
		for node in self.nodes:
			#print 'x coordinate of', node.id, 'is', node.coordinate_x
			#print 'y coordinate of', node.id, 'is', node.coordinate_y
			#print node.id,'(',node.num_id,'),',node.coordinate_x,',', node.coordinate_y
			#print
			FILE.write("n ")
			FILE.write(str(node.num_id))
			FILE.write(" ")
			FILE.write(str(node.coordinate_x))
			FILE.write(" ")
			FILE.write(str(node.coordinate_y))
			FILE.write("\n")
		for (n1,n2) in self.edges:
                        key=n1,"_",n2
			if key in edge_weights:
				eweight=edge_weights[n1,"_",n2]
			else:
				eweight=edge_weights[n2,"_",n1]
			to_print = '(' + str(n1) + ',' + str(n2) + ',' + str(eweight) + '), '
			#print to_print
			node1=self.getNode(n1)
			node2=self.getNode(n2)
			FILE.write("e ")
			FILE.write(str(node1.num_id))
			FILE.write(" ")
			FILE.write(str(node2.num_id))
			FILE.write(" ")
			FILE.write(str(eweight))
			FILE.write("\n")
		FILE.close()
		c.quit()
	
	def isEdge(self, node_id_1, node_id_2):
		if node_id_1 > node_id_2:
			# switch the two node-ids (edges are always saved with smaller id first)
			tmp = node_id_1
			node_id_1 = node_id_2
			node_id_2 = tmp
		# checks if there is an edge between two nodes
		for x in self.edges:
			if x == (node_id_1, node_id_2): return True
		return False
	
	def getNode(self, node_id):
		# returns the node for a given id
		for x in self.nodes:
			if x.getId() == node_id:
				return x
	
	def getNodes(self):
		return self.nodes
	
	def SetRandomNodePosition(self):
		# sets random positions for all nodes
		for node in self.nodes:
			node.coordinate_x = random.random() * center_distance - (center_distance/2)
			node.coordinate_y = random.random() * center_distance - (center_distance/2)
	
	def paintGraph(self):
		# (re)Paints the graph on the surface of the window
		
		# clear the screen
		for c_item in c.find_all():
			c.delete(c_item)
		
		# plot the energie vs time in the background of the window
		if show_energie_in_background == 1:
			if show_energies_in_background == 1:
				global all_energies
				energies_count = len(all_energies)
				# only show the last 200 energies at maximum
				if energies_count > 200:
					start_point = energies_count - 200
				else:
					start_point = 0
				for i in range(start_point, energies_count):
					c.create_rectangle(border+(c_width)/(energies_count-start_point)*(i-start_point), border+c_height-(c_height/highest_energy*all_energies[i]), border + (c_width)/(energies_count-start_point)+(c_width)/(energies_count-start_point)*(i-start_point), c_height+border, fill="#eee", outline="#ddd")
		
		
		
		
		# draw the coordinate system with the center
		# SARA: I'm commenting this for the paper...
		#c.create_line (border, c_height/2+border, (c_width+border), c_height/2+border, fill="#EEEEEE")
		#c.create_line (c_width/2+border, border, c_width/2+border, c_height+border*2+border, fill="#EEEEEE")
		
		# Output info via text
		if show_textinformation_in_background == 1:
			# opened file
			c.create_text(20, 40, anchor=tk.SW, text=str('opened file: ' +filename), font=("Helvectica", "10"), fill="#AAAAAA")
			# timestep
			c.create_text(20, 60, anchor=tk.SW, text=str('timestep: ' +str(timestep)), font=("Helvectica", "10"), fill="#AAAAAA")
			# overall energie
			c.create_text(20, 80, anchor=tk.SW, text=str('overall energie: ' +str(self.overall_energie)), font=("Helvectica", "10"), fill="#AAAAAA")
			c.create_text(20, 100, anchor=tk.SW, text=str('overall energie difference: ' +str(self.overall_energie_difference)), font=("Helvectica", "10"), fill="#AAAAAA")
			# number of components if more than one
			if self.connected_components_count > 1:
				c.create_text(20, 125, anchor=tk.SW, text=str('number of connected components: ' + str(self.connected_components_count)), font=("Helvectica", "14"), fill="#AAAAAA")
			# thermal_energie if there is still
			if thermal_energie > 0:
				c.create_text(20, 160, anchor=tk.SW, text=str('thermal energie: ' +str(thermal_energie)), font=("Helvectica", "20"), fill="#AAAAAA")
			# Calculation finished-message
			if self.calculation_finished:
				c.create_text(550, 60, anchor=tk.SW, text=str('Calculation finished after ' + str(timestep) + ' steps'), font=("Helvectica", "20"), fill="#000")
			# status message on the bottom of the screen
			if status_message != '':
				c.create_text(20, c_height, anchor=tk.SW, text=str(status_message), font=("Helvectica", "12"), fill="#000")
			
			# Show 'Now zooming out' if it is zoomed right now
			if zooming > 0:
				# Detect correct color for fade-out effect
				if zooming >= 40:
					color_string = "AAAAAA"
				if zooming >=30 and zooming < 40:
					color_string = "BBBBBB"
				if zooming >=20 and zooming < 30:
					color_string = "CCCCCC"
				if zooming >=10 and zooming < 20:
					color_string = "DDDDDD"
				if zooming >= 1 and zooming < 10:
					color_string = "EEEEEE"
				if zooming_out == 1:
					c.create_text(c_width/12+border, c_height/2+border, anchor=tk.SW, text=str('Now zooming out'), fill="#" + color_string, font=("Helvectica", "40"))
				else:
					c.create_text(c_width/12+border, c_height/2+border, anchor=tk.SW, text=str('Now zooming in'), fill="#" + color_string, font=("Helvectica", "40"))
		
		# DRAW AlL EDGES OF THE GRAPH
		for node in g.getNodes():
			# calculate position of this node
			x0 = ((node.coordinate_x*scaling_factor + (center_distance/2)) / center_distance * c_width) + border
			y0 = ((node.coordinate_y*scaling_factor + (center_distance/2)) / center_distance * c_height) + border
			# draw all the edges to neighbors of this node
			for neighbor_id in node.neighbour_ids:
				node2 = self.getNode(neighbor_id)
				if (node.id > node2.id):
					x1 = ((node2.coordinate_x*scaling_factor + (center_distance/2)) / center_distance * c_width) + border
					y1 = ((node2.coordinate_y*scaling_factor + (center_distance/2)) / center_distance * c_height) + border
					c.create_line (x0 + circle_diameter*scaling_factor / 2, y0 + circle_diameter*scaling_factor / 2, x1 + circle_diameter*scaling_factor / 2, y1 + circle_diameter*scaling_factor / 2)

		# DRAW AlL NODES OF THE GRAPH
		for node in g.getNodes():
			# calculate position of this node
			x0 = ((node.coordinate_x*scaling_factor + (center_distance/2)) / center_distance * c_width) + border
			y0 = ((node.coordinate_y*scaling_factor + (center_distance/2)) / center_distance * c_height) + border
			# draw this node
			fill_color = "AAA"
			if (node.cc_number <= 5):
				if (node.cc_number == 1):
					fill_color = "FFFFFF"	# green - 0C0
				if (node.cc_number == 2):
					fill_color = "00C"	# blue
				if (node.cc_number == 3):
					fill_color = "C00"	# red
				if (node.cc_number == 4):
					fill_color = "FF2"	# yellow
				if (node.cc_number == 5):
					fill_color = "FFB63D"	# orange
				if node.movable == 1:
					if node.isSeed:
						fill_color="000000"
					c.create_oval(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#" + fill_color)
				else:
					c.create_oval(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#000")
			else:
				if (node.cc_number == 6):
					fill_color = "FF2"	# yellow
				if (node.cc_number == 7):
					fill_color = "00C"	# blue
				if (node.cc_number == 8):
					fill_color = "C00"	# red
				if (node.cc_number == 9):
					fill_color = "0C0"	# green
				if node.movable == 1:
					c.create_rectangle(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#" + fill_color)
				else:
					c.create_rectangle(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#000")
			# write the id under the node
			## Original suma 20
			#Aqui estoy modificando para que no salgan los titulos, sino los ids numericos
			#SARA: commenting this for the paper...
			#c.create_text(x0, y0 + circle_diameter*scaling_factor, anchor=tk.SW, text=str(node.num_id))
			# c.create_text(x0, y0 + circle_diameter*scaling_factor + 40, anchor=tk.SW, text=str(node.cc_number), fill="#008800")
			
		 
		root.protocol("WM_DELETE_WINDOW", root.destroy)
		root.update()
	
	def calculateStep(self):
		new_overall_energie = 0
		
		# calculate the repulsive force for each node
		for node in self.nodes:
			node.force_coulomb = [0,0]
			for node2 in self.nodes:
				if (node.id != node2.id) and (node.cc_number == node2.cc_number):
					distance_x = (node.coordinate_x - node2.coordinate_x) 
					distance_y = (node.coordinate_y - node2.coordinate_y)
					radius = sqrt(distance_x*distance_x + distance_y*distance_y)
					if radius != 0:
						vector = [distance_x/radius, distance_y/radius]
						node.force_coulomb[0] += 0.02 * vector[0] / radius
						node.force_coulomb[1] += 0.02 * vector[1] / radius
						# add this force to the overall energie
						new_overall_energie += 0.02 / radius
					else:
						# if the nodes lie on each other, randomly replace them a bit
						node.force_coulomb[0] += random.random() - 0.5
						node.force_coulomb[1] += random.random() - 0.5
		
		# calculate the attractive force for each node
		##No se si aqui se pueda introducir el peso...
		for node in self.nodes:
			node.force_harmonic = [0,0]
			for neighbor_id in node.neighbour_ids:
				node2 = self.getNode(neighbor_id)
				mykey=neighbor_id,"_",node.id
				if mykey in edge_weights:
					eweight=edge_weights[neighbor_id,"_",node.id]
				else:
					eweight=edge_weights[node.id,"_",neighbor_id]
				distance_x = (node.coordinate_x - node2.coordinate_x)*float(eweight)
				distance_y = (node.coordinate_y - node2.coordinate_y)*float(eweight)
				radius = sqrt(distance_x*distance_x + distance_y*distance_y)
				if radius != 0:
					vector = [distance_x/radius* -1, distance_y/radius * -1]
					force_harmonic_x = vector[0] *radius*radius/100
					force_harmonic_y = vector[1] *radius*radius/100
				else:
					# if the nodes lie on each other, randomly replace them a bit
					force_harmonic_x = random.random() - 0.5
					force_harmonic_y = random.random() - 0.5
				node.force_harmonic[0] += force_harmonic_x
				node.force_harmonic[1] += force_harmonic_y
				# add this force to the overall energie
				new_overall_energie += radius*radius/100
				
		
		# calculate the difference between the old and new overall energie
		self.overall_energie_difference = self.overall_energie - new_overall_energie
		self.overall_energie = new_overall_energie
		all_energies.append(self.overall_energie)
		global highest_energy
		if self.overall_energie > highest_energy:
			highest_energy = self.overall_energie
		if not dont_finish_calculating:
			if (self.overall_energie_difference < energie_change_limit and self.overall_energie_difference > -1*energie_change_limit):
				self.calculation_finished = 1
		
		
		# set the new position influenced by the force
		global thermal_energie
		if timestep == 50 and thermal_energie > 0:
			thermal_energie = 0.2
		if timestep == 110 and thermal_energie > 0:
			thermal_energie = 0.1
		if timestep == 150 and thermal_energie > 0:
			thermal_energie = 0.0
		for node in self.nodes:
			(force_coulomb_x, force_coulomb_y) = node.force_coulomb
			(force_harmonic_x, force_harmonic_y) = node.force_harmonic
			# node.coordinate_x += force_coulomb_x + force_harmonic_x
			# node.coordinate_y += force_coulomb_y + force_harmonic_y
			
			node.velocity[0] += (force_coulomb_x + force_harmonic_x)*0.1
			node.velocity[1] += (force_coulomb_y + force_harmonic_y)*0.1
			# ensure maximum velocity
			if (node.velocity[0] > velocity_maximum):
				node.velocity[0] = velocity_maximum
			if (node.velocity[1] > velocity_maximum):
				node.velocity[1] = velocity_maximum
			if (node.velocity[0] < -1*velocity_maximum):
				node.velocity[0] = -1*velocity_maximum
			if (node.velocity[1] < -1*velocity_maximum):
				node.velocity[1] = -1*velocity_maximum
			# get friction into play
			if node.velocity[0] > friction:
				node.velocity[0] -= friction
			if node.velocity[0] < -1*friction:
				node.velocity[0] += friction
			if node.velocity[1] > friction:
				node.velocity[1] -= friction
			if node.velocity[1] < -1*friction:
				node.velocity[1] += friction
			
			# FINALLY SET THE NEW POSITION
			if node.id != grabed_node or node.cc_number == grabed_component:
				if node.movable == 1:
					node.coordinate_x += node.velocity[0]
					node.coordinate_y += node.velocity[1]
			
			if thermal_energie > 0:
				if node.movable == 1:
					node.coordinate_x += random.random()*thermal_energie*2-thermal_energie
					node.coordinate_y += random.random()*thermal_energie*2-thermal_energie
		
		# calculate centers for all connected components
		min_max = []
		center = []
		for i in range(0, self.connected_components_count):
			min_max.append([1000,1000,-1000,-1000])
		for i in range(0, self.connected_components_count):
			for node in self.getNodes():
				if node.cc_number == i+1:
					if node.coordinate_x < min_max[i][0]:
						min_max[i][0] = node.coordinate_x
					if node.coordinate_y < min_max[i][1]:
						min_max[i][1] = node.coordinate_y
					if node.coordinate_x > min_max[i][2]:
						min_max[i][2] = node.coordinate_x
					if node.coordinate_y > min_max[i][3]:
						min_max[i][3] = node.coordinate_y
			center.append([min_max[i][0] + (min_max[i][2] - min_max[i][0])/2, min_max[i][1] + (min_max[i][3] - min_max[i][1])/2])
		
		# if two components lie on each other, increase the distance between those
		for a in range(0, self.connected_components_count):
			for b in range(0, self.connected_components_count):
				# if a != b and center[a][0] > min_max[b][0] and center[a][0] < min_max[b][2] and center[a][1] > min_max[b][1] and center[a][1] < min_max[b][3]:
				if a != b:
					distance = 1
					if ((min_max[a][0]+distance > min_max[b][0] and min_max[a][0]-distance < min_max[b][2]) or (min_max[a][2]+distance > min_max[b][0] and min_max[a][2]-distance < min_max[b][2])) and ((min_max[a][1]+distance > min_max[b][1] and min_max[a][1]-distance < min_max[b][3]) or (min_max[a][3]+distance > min_max[b][1] and min_max[a][3]-distance < min_max[b][3])):
						# calculate replacement with help of the distance vector
						# of the centers
						distance_x = center[a][0] - center[b][0]
						distance_y = center[a][1] - center[b][1]
						radius = sqrt(distance_x*distance_x + distance_y*distance_y)
						replacement = [distance_x/radius* -1, distance_y/radius * -1]
						replacement[0] *= random.random() * -0.1
						replacement[1] *= random.random() * -0.1
						for node in self.nodes:
							if node.cc_number == a+1:
								if node.id != grabed_node:
									if node.movable == 1:
										node.coordinate_x += replacement[0]
										node.coordinate_y += replacement[1]
		
		# calculate the center of the graph and position all nodes new, so that 
		# the center becomes (0,0)
		x_max = -1000
		x_min = 1000
		y_max = -1000
		y_min = 1000
		for node in self.getNodes():
			if node.coordinate_x < x_min:
				x_min = node.coordinate_x
			if node.coordinate_x > x_max:
				x_max = node.coordinate_x
			if node.coordinate_y < y_min:
				y_min = node.coordinate_y
			if node.coordinate_y > y_max:
				y_max = node.coordinate_y
		center_x = x_min + (x_max - x_min)/2
		center_y = y_min + (y_max - y_min)/2
		for node in g.getNodes():
			if node.id != grabed_node:
				node.coordinate_x -= center_x
				node.coordinate_y -= center_y
		
		scale = 0
		# prevent nodes from leaving the screen - ZOOM OUT
		if (x_min < (center_distance/scaling_factor/-2)) or (y_min < (center_distance/scaling_factor/-2)) or (x_max > (center_distance/scaling_factor/2)):
			scale = 1
		# longer if-statement because node-caption is included
		if (y_max > (center_distance/scaling_factor/2)-((circle_diameter+20)*scaling_factor*center_distance/c_height)):
			scale = 1
		# zoom back in if necessary - ZOOM IN
		if (x_min - zoom_in_border > (center_distance/scaling_factor/-2)) and (y_min - zoom_in_border > (center_distance/scaling_factor/-2)) and (x_max + zoom_in_border < (center_distance/scaling_factor/2)) and (y_max + zoom_in_border < (center_distance/scaling_factor/2)-((circle_diameter+10)*scaling_factor*center_distance/c_height)):
			scale = -1
		
		if scale == 1:
			# zoom out
			global scaling_factor
			global zooming
			global zooming_out
			scaling_factor = scaling_factor * 0.99
			zooming = 50
			zooming_out = 1
		else:
			# zoom in
			if scale == -1:
				global scaling_factor
				global zooming
				global zooming_out
				scaling_factor = scaling_factor * 1.01
				zooming = 50
				zooming_out = 0
			else:
				# don't zoom (count down the fading for the zooming message)
				global zooming
				if zooming > 0:
					zooming -= 1
	
	def calculateConnectedComponents(self):
		# calculate the connected components of the graph
		all_node_ids = []
		for node in self.nodes:
			all_node_ids.append(node.id)
		visited_node_ids = []
		node_ids_to_process = []
		connected_component_number = 0
		while len(all_node_ids) > 0:
			# take an anchor node
			node_ids_to_process.append(all_node_ids.pop())
			connected_component_number += 1
			# process all nodes that are reachable from the anchor-node
			while len(node_ids_to_process) > 0:
				anchor_node_id = node_ids_to_process.pop()
				# set the anchors cc_number and add all neighbors to the process 
				# list that haven't been yet
				anchor_node = self.getNode(anchor_node_id)
				anchor_node.cc_number = connected_component_number
				for neighbor_node_id in anchor_node.neighbour_ids:
					if not neighbor_node_id in visited_node_ids:
						node_ids_to_process.append(neighbor_node_id)
						if neighbor_node_id in all_node_ids:
							all_node_ids.remove(neighbor_node_id)
				# this node is finished
				visited_node_ids.append(anchor_node_id)
		self.connected_components_count = connected_component_number
	
	def empty(self):
		self.clear()
	def clear(self):
		# deletes all nodes and edges in the graph
		self.nodes = []
		self.edges = []







# read lines of file with graph data ############################## LECTURA DEL ARCHIVO
print
print 'reading file', filename, 'with graph data ...'
try:
	f1 = open(filename, 'r')
	rows_graph = f1.readlines()
	f1.close()
except IOError:
	print filename, 'could not be opened'
	sys.exit(1)

# parse lines and build graph
print 'creating graph ...'
g = Graph()
curr_id=1

seed_line=rows_graph.pop(0).strip()
seed_array=seed_line.split()
(seed, seed_id)=seed_array
print 'SEED: ',seed_id

# find the line where the graph starts
for line in rows_graph:
	new_line = line.strip()
	line_array = new_line.split()
	if len(line_array) == 3:
	##	(node_1, node_2) = line_array
		(node_1, node_2, weight) = line_array
		g.addNode(node_1)
		g.addNode(node_2)
		g.addEdge(node_1, node_2, weight)


# Obtener el objeto del nodo semilla y habilitarlo
# Imprimir mensaje de comprobacion...
seed_node=g.getNode(seed_id)
seed_node.enableAsSeed()

# calculate the connected components:
g.calculateConnectedComponents()

# set the position of all nodes in the graph randomly to 
# a number between 0 and 10
g.SetRandomNodePosition()

# create the window object for painting the graph on
root = tk.Tk()

# make it cover the entire screen
##w, h = root.winfo_screenwidth(), root.winfo_screenheight()
#w, h = root.winfo_screenwidth()-30, root.winfo_screenheight()-30
#w,h=800,500
#SARA: for paper...
w,h=800,500
root.overrideredirect(1)
root.geometry("%dx%d+0+0" % (w, h))

c_width = w - border*2
c_height = h - border*2

root.title("Force directed layout of graphs (by Mathias Bader) - version 0.1")
c = tk.Canvas(root, width=c_width+2*border, height=c_height+2*border, bg='white')

c.pack()
c.focus_set()



g.paintGraph()
while (not g.calculation_finished or dont_finish_calculating):
	g.calculateStep()
	timestep += 1
	g.paintGraph()
g.paintGraph()

##Ver si aqui podemos escribir las coordenadas
g.printGraphData()
#g.printEdges()

c.update()
c.postscript(file="cluster.eps",colormode='color')

#Comentar la siguiente linea si no se desea que el programa se quede "congelado"
#c.mainloop()









