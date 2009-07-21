"""
Widget Library 0.1
Steve Johnson
srj15@case.edu
www.steveasleep.com
This code is in the public domain. Do whatever you like with it.
"""

import pyglet
import draw
from pyglet.window import key

class Widget(object):
    """Basic template for a widget."""
    def __init__(self, text, x, y, action):
        super(Widget, self).__init__()
    
    def draw():
        pass
    
    def on_key_press(self, symbol, modifiers):
        pass
    
    def on_key_release(self, symbol, modifiers):
        pass
    
    def on_mouse_motion(self, x, y, dx, dy):
        pass
    
    def on_mouse_press(self, x, y, button, modifiers):
        pass
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass
    
    def on_mouse_release(self, x, y, button, modifiers):
        pass
    
    def on_text(self, text):
        pass
    
    def on_text_motion(self, motion):
        pass
    
    def on_text_motion_select(self, motion):
        pass
    
    def mouse_is_over(self, x, y):
        return False
    

class TextButton(pyglet.text.Label):
    def __init__(self, text="", x=0, y=0, action=None, size=36, 
            anchor_x = 'left', anchor_y='baseline',
            color_normal=(128,128,128,255), color_mouse=(100, 100, 100, 255),
            color_pressed=(0, 0, 0, 255)):
        x, y = int(x), int(y)
        self.action = action
        self.color_normal = color_normal
        self.color_mouse = color_mouse
        self.color_pressed = color_pressed
        super(TextButton, self).__init__(
            text, font_name="Gill Sans",
            font_size=size, x=x, y=y, color=self.color_normal, 
            anchor_x=anchor_x, anchor_y=anchor_y
        )
        self.selected = False
    
    def on_mouse_motion(self, x, y, dx, dy):
        if self.mouse_is_over(x, y):
            self.color = self.color_mouse
            self.selected = True
        else:
            self.color = self.color_normal
            self.selected = False
    
    def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse_is_over(x, y):
            self.color = self.color_pressed
        else:
            self.color = self.color_normal
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.mouse_is_over(x, y):
            self.color = self.color_pressed
        else:
            self.color = self.color_normal
    
    def on_mouse_release(self, x, y, button, modifiers):
        self.color = self.color_normal
        if self.mouse_is_over(x, y) and self.action != None:
            self.action()
    
    def mouse_is_over(self, x, y):
        dy = self.document.get_font().descent
        x1, y1, x2, y2 = 0, 0, 0, 0
        
        if self.anchor_x == 'left':
            x1 = self.x
            x2 = self.x + self.content_width
        
        if self.anchor_x == 'right':    
            x1 = self.x - self.content_width
            x2 = self.x
            
        if self.anchor_x == 'center':
            x1 = self.x - self.content_width/2
            x2 = self.x + self.content_width
        
        if self.anchor_y == 'baseline':
            y1 = self.y + dy
            y2 = y1 + self.content_height
        if self.anchor_y == 'top':
            y1 = self.y - self.content_height
            y2 = self.y
        if self.anchor_y == 'center':
            y1 = self.y - self.content_height/2
            y2 = y1 + self.content_height
            
        return (x >= x1 and y >= y1 and x <= x2 and y <= y2)
    

class TextEntry(object):
    def __init__(
            self, text, x, y, width, accept_func=None, 
            align='left', color=(128, 128, 128, 255)):
        self.accept_func = accept_func
        
        self.ox = x
        self.y = y
        self.width = width
        self.accept_func = accept_func
        self.just = left
        self.original_text = text
        self.color_normal = color
        
        self.reset()
    
    def reset(self):    
        self.document = pyglet.text.document.UnformattedDocument(
            self.original_text
        )
        self.document.set_style(0, len(self.document.text), 
            dict(
                color=self.color_normal, align=self.just, 
                font_name='Gill Sans', font_size=36
            )
        )
        font = self.document.get_font()
        height = font.ascent - font.descent
        
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, self.width, height, multiline=False
        )
        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.position = len(self.original_text)
        
        self.reset_position()
    
    def draw(self):
        self.layout.draw()
    
    def reset_position(self):
        self.layout.y = self.y
        if self.anchor_x == 'center':
            self.layout.x = self.ox - self.layout.content_width/2
        elif self.anchor_x == 'right':
            self.layout.x = self.ox + self.layout.content_width/2
    
    def on_key_press(self, symbol, modifiers):
        self.reset_position()
        if symbol == key.RETURN or symbol == key.ENTER:
            if self.accept_func != None:
                self.accept_func(self.document.text)
                self.reset()
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
    
    def on_text(self, text):
        if len(self.document.text) >= 64: return
        self.caret.on_text(text)
        self.reset_position()
    
    def on_text_motion(self, motion):
        self.caret.on_text_motion(motion)
        self.reset_position()
    
    def on_text_motion_select(self, motion):
        self.caret.on_text_motion_select(motion)
        self.reset_position()
    

class KeyTrigger(object):
    def __init__(self, key, action):
        self.key = key
        self.action = action
    
    def draw(self):
        pass
    
    def on_key_release(self, symbol, modifiers):
        if symbol == self.key: self.action()
    

class ClickTrigger(object):
    def __init__(self, action):
        self.action = action
    
    def draw(self):
        pass
    
    def on_mouse_release(self, x, y, buttons, modifiers):
        self.action()
    

class HideableLabel(pyglet.text.Label):
    def __init__(self, show=False, *args, **kwargs):
        self.show = show
        super(HideableLabel, self).__init__(*args, **kwargs)
    
    def draw(self):
        if not self.show: return
        super(HideableLabel, self).draw()
    

class ImageButton(pyglet.sprite.Sprite):
    """docstring for ImageButton"""
    def __init__(self, img, x, y, action, rotation=0):
        super(ImageButton, self).__init__(img, x, y)
        self.action = action
        self.rotation = rotation
    
    def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse_is_over(x, y):
            self.color = (200, 200, 200)
            self.action()
            return pyglet.event.EVENT_HANDLED
        else:
            self.color = (255, 255, 255)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.mouse_is_over(x, y):
            return pyglet.event.EVENT_HANDLED            

    
    def on_mouse_motion(self, x, y, dx, dy):
        if self.mouse_is_over(x, y):
            self.color = (240, 240, 240)

        else:
            self.color = (255, 255, 255)

    
    def mouse_is_over(self, x, y):
        x1 = self.x-self.image.anchor_x
        y1 = self.y-self.image.anchor_y
        w = self.image.width
        h = self.image.height
        return (x >= x1 and y >= y1 and x < x1+w and y < y1+h)
    

class Slider(object):
    def __init__(self, x, y, action, position=0.0, width=200, size=20):
        self.x = x
        self.y = y
        self.action = action
        self.width = width
        self.size = size
        self.position = position
        self.dragging = False
        self.main_color = (0.5, 0.5, 0.5, 1)
        self.outline_color = (0, 0, 0, 1)
    
    def draw(self):
        draw.set_color(color=self.main_color)
        pyglet.gl.glLineWidth(2.0)
        draw.line(self.x, self.y, self.x+self.width, self.y)
        pyglet.gl.glLineWidth(1.0)
        slider_x = self.x + self.width * self.position
        draw.set_color(color=self.outline_color)
        pyglet.gl.glPointSize(self.size)
        draw.points((slider_x, self.y))
        draw.set_color(color=self.main_color)
        pyglet.gl.glPointSize(self.size-2)
        draw.points((slider_x, self.y))
    
    def update_position(self, x):
        self.position = (x-self.x)/self.width
        self.position = max(self.position, 0)
        self.position = min(self.position, 1)
    
    def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse_is_over(x, y):
            self.dragging = True
            self.update_position(x)
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dragging:
            self.update_position(x)
    
    def on_mouse_release(self, x, y, buttons, modifiers):
        if self.dragging:
            self.action(self.position)
            self.dragging = False
    
    def mouse_is_over(self, x, y):
        return (x >= self.x - self.size/2 and \
                y >= self.y - self.size/2 \
                and x <= self.x + self.width + self.size/2
                and y <= self.y + self.size/2)
    

class Line(object):
    def __init__(self, x1, y1, x2, y2, color=(0.7, 0.7, 0.7, 1)):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color
    
    def draw(self):
        draw.set_color(*self.color)
        draw.line(self.x1, self.y1, self.x2, self.y2)
    

class Rect(object):
    def __init__(self, x, y, w, h, color=(1,1,1,1)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
    
    def draw(self):
        draw.set_color(*self.color)
        draw.rect(self.x, self.y, self.x+self.w, self.y+self.h)
    

class RectOutline(Rect):
    def draw(self):
        draw.set_color(*self.color)
        draw.rect_outline(self.x, self.y, self.x+self.w, self.y+self.h)
    
