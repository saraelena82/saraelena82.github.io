# gradient.py
# Authors: Schaeffer & Garza
# Usage: gradient.py [cloud file] [year file] [dest file base name]

import Tkinter as tk
import tkFont
import random
import math
import sys
#from math import floor, ceil
#from Tkinter import *
from colorbar import *

years={}
base_year=2010 #Para DBLP

def paint_gradient(label,fontsize,x1,y1,x2,y2,vector,canvas):
    #green=150
    dx1=float(x1)
    dy1=float(y1)
    dx2=float(x2)
    dy2=float(y2)
    w=int(floor(abs(dx1-dx2)))
    h=int(floor(abs(dy1-dy2)))
    n = len(vector)
    step = w / n
    m = (w - n * step) / 2
    gap = step / 3
    pos = dx1
    while len(vector) > 0:
        value = vector.pop(0)
        count = 1
        while len(vector) > 0 and vector[0] == value:
            count += 1
            vector.pop(0)
        color = int(floor((1.0 - value) * 255))
        width = count * step
        if len(vector) > 0: # last
            width -= gap 
        canvas.create_rectangle(pos, dy1, pos+width, dy2, \
                                 fill = '#%02x%02x%02x' % (color, color, color), \
                                 width = 0, outline="")
        pos += width
        if len(vector) > 0: # transition
            shade = makeShading(color, int(floor((1.0 -  vector[0]) * 255)), 2 * gap)
            for pixel in xrange(2 * gap): # pixel por pixel
                c = shade[pixel]
                canvas.create_rectangle(pos + pixel, dy1, pos + pixel + 1, \
                                         dy2, fill = '#%02x%02x%02x' % (c, c, c), \
                                         width = 0, outline="")
            pos += 2 * gap
    label = canvas.create_text(dx1+0.5, dy1+0.5, fill = 'white', \
                                anchor = NW, justify = CENTER, \
                                font = ('Arial', fontsize), \
                                text = label)

    

def map_year_score(year):
    difference=abs(base_year-year)

    if difference>100:
        return 0.0
    else:
        return pow(1-difference/100.0,3)
    """if difference>20:
        return 0.1
    elif 10<=difference and difference<=20:
        return 0.45
    elif 10<difference and difference<=5:
        return 0.9"""

#Create gradient vector for cloud tag (label)
#Inputs:
#      label - cloud tag
#      x1    - x coordinate of superior left corner
#      y1    - y coordinate of superior left corner
#      x2    - x coordinate of inferior right corner
#      y2    - y coordinate of inferior right corner
#      cv    - canvas
def create_gradient(label,x1,y1,x2,y2,cv,year_string):
    var=1
    vector=list()
        
    word_years=year_string.split() #Se guarda una lista de un solo elemento, que es un string con todos los anios
    var=len(word_years)
    for i in range(0,var):
        normalized_score=map_year_score(int(word_years[i]))
        #print word_years[i],' ',normalized_score
        vector.append(normalized_score)
    
    vector.sort()
    return vector

#TODO: Crear objetos con los datos, en lugar de manejarlos sueltos...
def createXMLTag(label,fsize,x1,y1,x2,y2,year_string,FILE):
    w_years=year_string.split()
    FILE.write(" <element>\n")
    FILE.write("  <word>"+label+"</word>\n")
    FILE.write("  <size>"+str(fsize)+"</size>\n")
    #FILE.write("  <coordinates>\n")
    FILE.write("   <x1>"+str(x1)+"</x1>\n")
    FILE.write("   <y1>"+str(y1)+"</y1>\n")
    FILE.write("   <x2>"+str(x2)+"</x2>\n")
    FILE.write("   <y2>"+str(y2)+"</y2>\n")
    #FILE.write("  </coordinates>\n")
    #FILE.write("  <years>\n")
    for year in w_years:
        FILE.write("   <year>"+str(year)+"</year>\n")
    #FILE.write("   </years>\n")
    FILE.write(" </element>\n")

def main():
    if (len(sys.argv)<4):
        print "Usage: gradient.py [cloud file] [year file] [dest file base name]"
        sys.exit(1)

    cloudXMLFile=sys.argv[3] + "_cloud.xml"
    XMLFile=open(cloudXMLFile,"w")
    XMLFile.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n") #Espero no tengamos problemas con el encoding...
                
    root = tk.Tk()
    #Color cielo
    #bg="#3366CC"
    c = tk.Canvas(root, width=1000, height=500)
    #c = tk.Canvas(root, width=root.winfo_screenwidth()-30, height=root.winfo_screenheight()-30)
    c.pack()

    print 'reading year file ...'
    try:
            f1 = open(sys.argv[2], 'r')
            rows = f1.readlines()
            f1.close()
    except IOError:
            print 'file could not be opened'
            sys.exit(1)

    for line in rows:
            line=line.split(',')
            title=line[0]
            years[title]=line[1:]

    print 'reading cloud file ...'
    try:
            f1 = open(sys.argv[1], 'r')
            rows = f1.readlines()
            f1.close()
    except IOError:
            print 'file could not be opened'
            sys.exit(1)

    for line in rows:
            new_line = line.strip()
            try:
                line_array = new_line.split()
                (label,fsize,x1,x2,y1,y2) = line_array
            except ValueError:
                continue

            #Guardar en archivo XML
            if label in years:
                word_year_string=years[label][0].strip() #Se guarda una lista de un solo elemento, que es un string con todos los anios
                g_vector=create_gradient(label,x1,y1,x2,y2,c,word_year_string)
                paint_gradient(label,fsize,x1,y1,x2,y2,g_vector,c)
                #c.create_text(x1, y1, anchor=tk.NW, text=label, fill="#FFFFFF", font= ("Arial", fsize))
                #box = gradientBox(c,label,int(fsize),g_vector)
                #box.place(x=x1,y=y1)
                #writeXML(label,x1,y1,x2,y2,years[label][0]);
                #print label+","+fsize+","+x1+","+x2+","+y1+","+y2+","+word_year_string
                createXMLTag(label,fsize,x1,x2,y1,y2,word_year_string,XMLFile);
            else:
                print 'Did not find value for ',label
    #La unica va a ser dibujar directamente aqui...
    c.update()
    c.postscript(file=sys.argv[3]+"_gradient.eps", colormode='color')
    #c.mainloop()

    XMLFile.write("</xml>")
    XMLFile.close()

main()

