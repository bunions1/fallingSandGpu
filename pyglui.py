"""
Pyglui v0.11
by Steve Johnson
srj15@case.edu
www.steveasleep.com
This code is in the public domain. Do whatever you like with it.
"""

import pyglet

current_card = None
last_card = None
next_card = None
transition_time = 0.0
window = None
fade_color = (1,1,1)
fade_time = 0.5

pushed = False

load_path = ""

def init(win, start_card, fadecol=(1,1,1), fadetime=0.5):
    global window, current_card, fade_color, fade_time
    window = win
    current_card = start_card
    fade_color = fadecol
    fade_time = fadetime
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    push_handlers()

class Card(object):
    def __init__(self, widgets):
        super(Card, self).__init__()
        self.widgets = widgets
    
    def push_handlers(self):    
        for widget in self.widgets:
            window.push_handlers(widget)
    
    def pop_handlers(self):
        for widget in self.widgets:
            window.pop_handlers()
        
    def draw(self):
        for widget in self.widgets:
            widget.draw()
    

class LiveCard(Card):
    def __init__(self, widget_func):
        super(LiveCard, self).__init__(widget_func())
        self.widget_func = widget_func
    
    def push_handlers(self):
        self.widgets = self.widget_func()
        super(LiveCard, self).push_handlers()
    
    def refresh(self):
        self.pop_handlers()
        self.push_handlers()
    

def card_magic(mystery_variable):
    if hasattr(mystery_variable, '__call__'):
        return LiveCard(mystery_variable)
    elif isinstance(mystery_variable, list):
        return Card(mystery_variable)
    elif isinstance(mystery_variable, Card):
        return mystery_variable

def push_handlers():
    global pushed
    if pushed:
        print "event push mismatch"
        return
    pushed = True
    current_card.push_handlers()

def pop_handlers():
    global pushed
    if not pushed:
        print "event pop mismatch"
        return
    pushed = False
    current_card.pop_handlers()

def draw_rect(x1, y1, x2, y2):
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2f', (x1, y1, x1, y2, x2, y2, x2, y1)))

def draw_gui(dt=0):
    global last_card, current_card, next_card, transition_time
    try:
        current_card.draw()
    except:
        pass
    if transition_time > 0:
        if next_card != None:
            a = (1.0-transition_time/fade_time)
        else:
            a = transition_time/fade_time
        pyglet.gl.glColor4f(fade_color[0],fade_color[1],fade_color[2],a)
        draw_rect(0, 0, window.width, window.height)
        transition_time -= dt
        if transition_time <= 0:
            if next_card != None:
                last_card = current_card
                current_card = next_card
                next_card = None
                transition_time = fade_time
            else:
                transition_time = 0.0
                push_handlers()

def change_to_card(something):
    global next_card, transition_time
    pop_handlers()
    next_card = card_magic(something)
    transition_time = fade_time

def change_to_card_fast(something):
    global last_card, current_card, next_card
    pop_handlers()
    last_card = current_card
    current_card = card_magic(something)
    next_card = None
    push_handlers()

def get_card_changer(something):
    def change():
        change_to_card(something)
    return change

def get_fast_card_changer(something):
    def change():
        change_to_card_fast(something)
    return change

def go_back():
    global next_card, transition_time
    pop_handlers()
    next_card = last_card
    transition_time = fade_time

def go_back_fast():
    global last_card, current_card, next_card
    pop_handlers()
    last_card, current_card = current_card, last_card
    next_card = None
    push_handlers()
