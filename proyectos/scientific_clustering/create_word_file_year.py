import sys
import string
import math
import collections
from os.path import *
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer

#TODO: acoplar este archivo con preproc_author_graph

def lemmatize(words):
    unique_words=set([])
    lemmatizer=WordNetLemmatizer()
    for w in words:
        lemma=lemmatizer.lemmatize(w)
        unique_words.add(lemma)
    words=list(unique_words)
    return words
        
def remove_punctuation(words):
    new_words=[]
    for w in words:
        w=w.strip(string.punctuation)
        new_words.append(w)
    return new_words

def remove_stopwords(words):
    meaningful_words=[]
    for w in words:
        if not w.lower() in stopwords.words('english'):
            meaningful_words.append(w)

    return meaningful_words


def process_title(title):
    if title[0:1]=='_':
            title=title[1:]
    words=title.split('_')
    words.sort()
    return words

if (len(sys.argv)<4):
    print "Usage: create_word_file_year [source file] [lower limit] [upper limit] "
    sys.exit(1)

s=set([])
title_year={} #(article title, year published)
fname=basename(sys.argv[1])
bname=splitext(fname)[0]
lower=int(sys.argv[2])
upper=int(sys.argv[3])
nodes=bname + "_nodes.dat"
edges=bname + "_edges.dat"
wyears=bname + "_years.dat"
coc={}
wordfreq={}
filtered_words={}
filtered_coc={}
average=0.0
wordcount=0
maxf=-1
minf=10000
years={} #(word, years)

print 'reading file'
try:
    cluster_file=open(sys.argv[1],'r')
    rows=cluster_file.readlines()
    cluster_file.close()
except IOError:
    print 'file could not be opened'
    sys.exit(1)

n=int(rows[0])
m=len(rows)-n-1
print 'n: ',n,' m:',m

#Leemos los vertices
for k in range(2,n+1):
    new_line=rows[k].strip()
    try:
        components=new_line.split()
        title=components[1]
        length_projection=int(components[2])
        year=components[3] #A title is linked to only one year
        words=lemmatize(remove_stopwords(remove_punctuation(process_title(title))))
        for w in words:
            if w in wordfreq:
                wordfreq[w]=wordfreq[w] + 1
            else:
                wordfreq[w]=1
            if w in years: #Agrego el anio
                years[w]=years[w] + " " + str(year)
            else:
                years[w]=str(year)
        for i in range(len(words)-1):  #Saco la co-ocurrencia de los bigramas en cada etiqueta
            for j in range(i+1, len(words)):
                bigram=words[i] + '_' + words[j]
                ibigram=words[j] + '_' + words[i]
                if bigram in coc:
                    coc[bigram]=coc[bigram] + 2 #Agregamos una mayor fuerza cuando las palabras co-ocurren en el mismo titulo
                    average=average+2 #TODO: Checar si esto es lo correcto...
                elif ibigram in coc:
                    coc[ibigram]=coc[ibigram] + 2
                    average=average+2
                else:
                    coc[bigram]=2
                    average=average+2
    except ValueError:
        print "Value error"
        continue

#Cuando no hay un maximo como tal, todas las etiquetas obtienen el tam. maximo de letra. Por tanto, ponemos una condicion...
for k in wordfreq.keys():
    if wordfreq[k]>maxf:
        maxf=wordfreq[k]
    elif wordfreq[k]<minf:
        minf=wordfreq[k]

if maxf-minf==0:
    maxf=10

for k in wordfreq.keys():
    wordfreq[k]=wordfreq[k]*1.0/maxf #Si todos los terminos tienen la misma frecuencia, se mapea el tam. mas grande de letra...

#TODO: PONER TODO ESTO EN INGLES
#Esto es para ordenar las palabras de la mas a la menos frecuente
ordered_words=collections.OrderedDict(sorted(wordfreq.items(), key=lambda t: t[1])) #Podriamos usar reversed sino fuera por el pop

#Range validations
if lower<0:
    lower=0

if upper>len(ordered_words):
    upper=len(ordered_words)

if upper<lower:
    temp=lower
    lower=upper
    upper=temp

#Si el rango no empieza en 0, hacemos pop hasta llegar al numero deseado
for i in range(0, lower):
    ordered_words.popitem()

for i in range(lower, upper):
    oitem=ordered_words.popitem()
    filtered_words[oitem[0]]=oitem[1]
    #print oitem[0],' ',oitem[1]

#Write year file
YFILE=open(wyears,"w")
for k in filtered_words.keys():
    #print k,',',years[k]
    YFILE.write(k)
    YFILE.write(", ")
    YFILE.write(str(years[k]))
    YFILE.write("\n")

YFILE.close()

#Escribo los nodos
#TODO: Checar si hacer el tam. de letra antes o despues del filtro
print "+++Writing nodes+++"
NFILE=open(nodes,"w")
for k in filtered_words.keys():
    filtered_words[k]=int(math.floor(filtered_words[k]*(30-10+1)) + 10) #10 es el tamanio minimo de letra y 30 el maximo permitido
    #print k,' ',filtered_words[k]
    NFILE.write(k)
    NFILE.write(" ")
    NFILE.write(str(filtered_words[k]))
    NFILE.write("\n")

NFILE.close()


#for w in coc.keys():
#    print w,' ',coc[w]

#print "#########################"

for k in range(n+2, len(rows)):
    new_line=rows[k].strip()
    #print new_line
    (etype,title1,title2,simm,art_num)=new_line.split() #TODO: Check line contents
    words1=process_title(title1)
    words2=process_title(title2)
    for w1 in words1:
        for w2 in words2:
            if w1!=w2:
                bigram=w1 + '_' + w2
                ibigram=w2 + '_' + w1
                #print bigram
                #print ibigram
                if bigram in coc:
                    coc[bigram]=coc[bigram]+1
                    average=average+1
                elif ibigram in coc:
                    coc[ibigram]=coc[ibigram]+1
                    average=average+1
                else:
                    coc[bigram]=1
                    average=average+1
                

#for w in wordfreq.keys():
#    print w,' ',wordfreq[w]

#for w in coc.keys():
#    print w,' ',coc[w]

average/=len(coc)

for k in coc.keys():
    terms=k.split('_')
    if terms[0] in filtered_words.keys() and terms[1] in filtered_words.keys():
        #print k,' ',coc[k]
        filtered_coc[k]=coc[k]


#Escribo las aristas
print "+++Writing edges+++"
EFILE=open(edges,"w")
for k in filtered_coc.keys():
    filtered_coc[k]=filtered_coc[k]*1.0/average
    #print k,' ',filtered_coc[k]
    terms=k.split('_')
    EFILE.write(terms[0])
    EFILE.write(" ")
    EFILE.write(terms[1])
    EFILE.write(" ")
    EFILE.write(str(filtered_coc[k]))
    EFILE.write("\n")

EFILE.close()


'''for title in title_year.keys():
    print title,' ',title_year[title]



average/=len(coc)
#print average


for f in filtered_words.keys(): #Parece que no se conserva el orden, pero lo que nos interesa es simplemente contener las palabras mas frecuentes
    print f,' ',filtered_words[f]

print 

"""for k in coc.keys():
    print k,' ',coc[k]

print """

'''
