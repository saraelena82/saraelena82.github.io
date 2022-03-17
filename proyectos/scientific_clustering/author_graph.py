import Tkinter as tk
import tkFont
import random
import math
import sys
from math import floor, ceil
#import Pmw
#from colorball import *
        
#Aqui lo que estamos haciendo es obtener circulos a partir del mapa de etiquetas (generado con force_layout_tags.py)
#argv[1] = cloud
#argv[2] = years

#Plan B: Ya que un autor puede tener asociados muchos anios y su centralidad no necesariamente es grande, por lo pronto vamos a generar 3 clases:
# Clase 1: Nuevo -- consiste en autores que han publicado solo en anios recientes
# Clase 2: Viejo -- consiste en autores que han publicado solo en anios anteriores
# Clase 3: Vigente -- consiste en autores que han publicado a lo largo del tiempo, i.e. en anios anteriores y recientes
# Teniendo el vector de anios, se revisa el primer elemento. Si es viejo (de acuerdo a un anio base y un umbral), se procede a checar el ultimo;
#  si este tambien es viejo, esta sera la clase asignada. Lo mismo en caso de que el primer elemento sea nuevo (primero es nuevo y ultimo tambien). Sin embargo,
#  si se detecta un cambio (viejo-nuevo), la clase sera 'vigente'.

circles={}
years={}
base_year=2010

def assign_year_class(threshold, baseyear, pubyear):
    if abs(baseyear-pubyear)>threshold:
        yclass="viejo"
    else:
        yclass="nuevo"
    return yclass

def assign_color(yearvector):
    #colors={'nuevo':'#0AFB0A','viejo':'#668866','vigente':'#1E881E'}
    colors={'nuevo':'#000000','viejo':'#FFFFFF','vigente':'#C0C0C0'}
    yearvector.sort()

    first=int(yearvector[0]) #First publication year of the vector
    last=int(yearvector[len(yearvector)-1])

    author_class1=assign_year_class(10,base_year,first)
    author_class2=assign_year_class(10,base_year,last)
    
    if author_class1==author_class2:
        return colors[author_class1]
    else:
        return colors["vigente"]

def makeShading(initial, final, length):
    span = final - initial 
    step = (1.0 * span) / length
    shade = list()
    value = initial
    for i in xrange(length):
        shade.append(floor(value))
        value += step
    return shade

def gradientBall(box, size, vector, label_id, offsetx, offsety):
    #global MARGIN
    MARGIN=int(floor(size*0.05))
    #Aqui tambien le movi para hacer mas grande el canvas... (por lo pronto)
    #box = Canvas(parent, width = size, height = size, \
    #                 borderwidth = 0)
    n = len(vector)
    size -= 2 * MARGIN
    step = (size / 2) / n
    assert(step > 0)
    #print 'step: ',step
    c = size / 2 + MARGIN # centro
    r = n
    color = None
    while r > 0:
        anterior = color
        value = vector.pop() # last out first
        count = 1
        while len(vector) > 0 and vector[-1] == value:
            count += 1
            vector.pop()
        color = int(floor((1.0 - value) * 255))
        rad = r * step
        gap = rad / 3 + 1
        resta = rad
        if r < n: # no es primero
	    #print 'gap: ',gap
            shade = makeShading(anterior, color, 2*gap)
            for pixel in xrange(gap): # pixel por pixel
                col = shade[pixel]
                pos = c - rad
                fin = pos + (rad * 2)
                rad -= 1
                box.create_oval(pos+offsetx, pos+offsety, fin+offsetx, fin+offsety, \
                                    fill = '#%02x%02x%02x' % (color, 255, color), \
                                    width = 0)
            resta -= gap
        if len(vector) == 0: # es el ultimo
            resta += gap
        rad = resta
        pos = c - rad
        fin = pos + (2 * rad)
        box.create_oval(pos+offsetx, pos+offsety, fin+offsetx, fin+offsety, \
                            fill = '#%02x%02x%02x' % (color, 150, color), \
                            width = 0,tags=label_id)
        r -= count
        #print "r:",r

        #balloon=Pmw.Balloon(box)
        #balloon.tagbind(box,label_id,label(label_id))

def map_year_score(year):
    difference=abs(base_year-year)

    if difference>100:
        return 0.0
    else:
        return pow(1-difference/100.0,3)

def get_word_years(label):
    if label in years:
        word_years=years[label][0].split() #Se guarda una lista de un solo elemento, que es un string con todos los anios
    else:
        print 'Did not find value for ',label
        word_years=[]

    return word_years

def create_gradient(label, cv):
    vector=list()
    avg_score=0

    word_years=get_word_years(label)
    var=len(word_years)

    for i in range(0,var):
        normalized_score=map_year_score(int(word_years[i]))
        #print word_years[i],' ',normalized_score
        avg_score=avg_score+normalized_score

    avg_score=avg_score/var
    print "AVERAGE SCORE= ",avg_score
    vector.append(avg_score)

    vector.sort()
    return vector

def read_file(filename, flabel):
	print 'reading',flabel,' file ...'
	try:
		f1 = open(filename, 'r')
		rows = f1.readlines()
		f1.close()
		return rows
	except IOError:
		print 'file could not be opened'
		sys.exit(1)


class Circle:
        def __init__(self,posx,posy,radius):
                self.posx=posx
                self.posy=posy
                self.radius=radius
        #Get circle middle point coordinate x
        def get_middle_x(self):
                return self.posx + radius
        def get_middle_y(self):
                return self.posy + radius
	def get_posx(self):
		return self.posx
	def get_posy(self):
		return self.posy
	def get_radius(self):
		return self.radius

root = tk.Tk()
#c = tk.Canvas(root, width=1000, height=500)
c = tk.Canvas(root, width=root.winfo_screenwidth()-30, height=root.winfo_screenheight()-30)
c.pack()

#c.create_rectangle(0,0,1000,500,fill="blue")
yrows=read_file(sys.argv[2],"years")

for line in yrows:
        line=line.split(',')
        title=line[0]
        years[title]=line[1:]

crows=read_file(sys.argv[1],"cloud")

for line in crows:
	new_line = line.strip()
	try:
            line_array = new_line.split()
	    (label,fsize,x1,x2,y1,y2) = line_array
        except ValueError:
            continue
        dx1=float(x1)
        dx2=float(x2)
        dy2=float(y2)
        dy1=float(y1)
        diameter=abs(dy2-dy1) #Me parece apropiado para este contexto el usar la altura de la etiqueta
        radius=diameter/2.0
        #print 'diameter: ',diameter
	circ=Circle(dx1,dy1,radius)
	circles[label]=circ
	#balloon=Pmw.Balloon(c)
	#balloon.tagbind(c,label,label)

erows=read_file(sys.argv[3],"edges")

for line in erows:
        new_line = line.strip()
        try:
            line_array = new_line.split()
	    (v1,v2,weight) = line_array
	    #print v1,' ',v2,' ',weight
        except ValueError:
	    print "Error"
            continue
        c1=circles[v1]
        c2=circles[v2]
        c.create_line(c1.get_middle_x(),c1.get_middle_y(),c2.get_middle_x(),c2.get_middle_y(),width=float(weight),fill="#000000")
	#print c1.get_middle_x(),' ',c1.get_middle_y(),' ',c2.get_middle_x(),' ',c2.get_middle_y()

font = tkFont.Font(family="Arial", size=11)

for circ in circles.keys():
	diameter=circles[circ].get_radius()*2
        posx=circles[circ].get_posx()
        posy=circles[circ].get_posy()
	#g_vector=create_gradient(circ,c)
	#gradientBall(c,int(math.ceil(diameter)),g_vector,circ,circles[circ].get_posx(),circles[circ].get_posy())
        author_years=get_word_years(circ)
        author_color=assign_color(author_years)
        c.create_oval(posx, posy, posx+diameter, posy+diameter, fill=author_color)
	pinitx=circles[circ].get_middle_x() + circles[circ].get_radius() + 5
	pinity=circles[circ].get_middle_y()
	(fw,fh) = (font.measure(circ),font.metrics("linespace"))
	c.create_rectangle(pinitx,pinity,pinitx+fw,pinity+fh,fill="#FFFFFF",outline="")  #FBF7D9
	c.create_text(pinitx, pinity,text=circ,anchor=tk.NW,fill="#000000",font= ("Arial", 16)) #Anteriormente era 11

#Modes for eps: color, gray, mono
c.update()
c.postscript(file="circles.eps",colormode='color')
#c.mainloop()
