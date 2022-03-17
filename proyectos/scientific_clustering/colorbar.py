from Tkinter import *
from math import floor

DIM = 500
MARGIN = 5
MULT = 1.1
vis = None

def makeShading(initial, final, length):
    span = final - initial 
    step = (1.0 * span) / length
    shade = list()
    value = initial
    for i in xrange(length):
        shade.append(floor(value))
        value += step
    return shade

def gradientBox(parent, content, ptsize, vector):
    global vis, MARGIN, MULT
    w = ptsize * len(content) + 2 * MARGIN # approx
    h = ptsize + 2 * MARGIN # approx
    box = Canvas(parent, width = w, height = h,borderwidth=-2)
    label = box.create_text(0, 0, \
                                anchor = NW, justify = CENTER, \
                                font = ('Arial', ptsize), \
                                text = content)
    (x1, y1, x2, y2) = box.bbox(label)
    box.delete(label)
    w = int(floor(MULT * (x2 - x1) + 2 * MARGIN)) 
    h = int(floor(MULT * (y2 - y1) + 2 * MARGIN))
    box.config(width = w, height = h)
    box.grid(row = 0,column = 0)
    n = len(vector)
    step = w / n
    m = (w - n * step) / 2
    gap = step / 3
    pos = m
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
        box.create_rectangle(pos, 0, pos + width, h, \
                                 fill = '#%02x%02x%02x' % (color, color, color), \
                                 width = 0)
        pos += width
        if len(vector) > 0: # transition
            shade = makeShading(color, int(floor((1.0 -  vector[0]) * 255)), 2 * gap)
            for pixel in xrange(2 * gap): # pixel por pixel
                c = shade[pixel]
                box.create_rectangle(pos + pixel, 0, pos + pixel + 1, \
                                         h, fill = '#%02x%02x%02x' % (c, c, c), \
                                         width = 0)
            pos += 2 * gap
    label = box.create_text(w/2, h/2, fill = 'white', \
                                anchor = CENTER, justify = CENTER, \
                                font = ('Arial', ptsize), \
                                text = content)
    return box

def placeBox(canvas):
    text = raw_input('Type text to place: ')
    if text == 'quit':
        return
    x = float(raw_input('Type relative horizontal position [0-1]: '))
    y = float(raw_input('Type relative vertical position [0-1]): '))
    pt = int(raw_input('Type text size: '))
    data = raw_input('Type sorted color vector [0-1]: ')
    vector = list()
    for d in data.split():
        vector.append(float(d))
    box = gradientBox(canvas, text, pt, vector)
    box.place(relx = x, rely = y)
    vis.after(100, placeBox, canvas)
    return

def main():
    global vis, DIM
    vis = Tk()
    canvas = Canvas(vis, width = DIM, height = DIM)
    canvas.pack()
    vis.after(50, placeBox, canvas)
    vis.mainloop()
    
if __name__ == '__main__':
    main()
