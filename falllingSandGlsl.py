import pprint
pp = pprint.PrettyPrinter(indent=4)
import sys
print sys.path
import sys
import time
from ctypes import *
from exceptions import *
import random

# disable error checking (python -O) to make this code work :)
from pyglet import options
import pyglet.window
from pyglet import clock
from pyglet.gl import *
from pyglet.image import *
from  pyglet.sprite import *
from pyglet.window import mouse
#from  pyglet.text import *
print pyglet.version
from  shader import *
import pyglui
import draw
import widget




c_float4 = c_float * 4



class Failed(Exception): pass

class TextureParam(object):
    max_anisotropy = 0.0

    FILTER   = 1
    LOD      = 2
    MIPMAP   = 4
    WRAP     = 8
    BORDER   = 16
    PRIORITY = 32
    ALL      = 63

    def __init__(self, wrap = GL_REPEAT, filter = GL_LINEAR, min_filter = None):
        if self.max_anisotropy == 0.0 and \
           gl_info.have_extension('GL_EXT_texture_filter_anisotropic'):
            v = c_float()
            glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, byref(v))
            self.max_anisotropy = v.value

        if min_filter is None: min_filter = filter
        self.min_filter = min_filter
        self.mag_filter = filter
        self.min_lod = -1000
        self.max_lod = 1000
        self.min_mipmap = 0
        self.max_mipmap = 1000
        self.wrap_s = wrap
        self.wrap_t = wrap
        self.wrap_r = wrap
        self.priority = 0
        self.anisotropy = 1.0
        self.border_colour = c_float4(0.0, 0.0, 0.0, 0.0)

    def applyToCurrentTexture(self, target, flags = ALL):
        
        if flags & self.FILTER:
            glTexParameteri(target, GL_TEXTURE_MIN_FILTER, self.min_filter)
            glTexParameteri(target, GL_TEXTURE_MAG_FILTER, self.mag_filter)
        if self.max_anisotropy > 0.0:
            glTexParameterf(target, GL_TEXTURE_MAX_ANISOTROPY_EXT, self.anisotropy)
            
#        if flags & self.LOD:
#            glTexParameterf(target, GL_TEXTURE_MIN_LOD, self.min_lod)
#            glTexParameterf(target, GL_TEXTURE_MAX_LOD, self.max_lod)
#        if flags & self.MIPMAP:
#            glTexParameteri(target, GL_TEXTURE_BASE_LEVEL, self.min_mipmap)
#            glTexParameteri(target, GL_TEXTURE_MAX_LEVEL, self.max_mipmap)

        if flags & self.WRAP:
            glTexParameteri(target, GL_TEXTURE_WRAP_S, self.wrap_s)
            glTexParameteri(target, GL_TEXTURE_WRAP_T, self.wrap_t)
            glTexParameteri(target, GL_TEXTURE_WRAP_R, self.wrap_r)
            
        if flags & self.BORDER:
            glTexParameterfv(target, GL_TEXTURE_BORDER_COLOR, self.border_colour)
        if flags & self.PRIORITY:
            glTexParameterf(target, GL_TEXTURE_PRIORITY, self.priority)


class Surface(object):
    SURF_NONE          = 0
    SURF_COLOUR        = 2
    SURF_DEPTH         = 3
    SURF_STENCIL       = 4
    SURF_DEPTH_STENCIL = 5

    DEFAULTS = {
        SURF_COLOUR:
            (GL_RGBA,                 GL_TEXTURE_2D,       True,  False),
        SURF_DEPTH:
            (GL_DEPTH_COMPONENT24,    GL_RENDERBUFFER_EXT, False, False),
        SURF_STENCIL:
            (GL_STENCIL_INDEX8_EXT,   GL_RENDERBUFFER_EXT, False, False),
        SURF_DEPTH_STENCIL:
            (GL_DEPTH24_STENCIL8_EXT, GL_RENDERBUFFER_EXT, False, False)
    }

    def __init__(self, surface_type = SURF_NONE, gl_fmt = None,
            gl_tgt = None, is_texture = None, is_mipmapped = None,
            params = None):
        self.gl_id = 0

        d = self.DEFAULTS[surface_type]
        if gl_fmt is None: gl_fmt = d[0]
        if gl_tgt is None: gl_tgt = d[1]
        if is_texture is None: is_texture = d[2]
        if is_mipmapped is None: is_mipmapped = d[3]
        if params is None: params = TextureParam()

        self.surface_type = surface_type
        self.gl_fmt = gl_fmt
        self.gl_tgt = gl_tgt
        self.is_texture = is_texture
        self.is_mipmapped = is_mipmapped

        self.params = params

    def bind(self):
        glBindTexture(self.gl_tgt, self.gl_id)

    def enableAndBind(self):
        glEnable(self.gl_tgt)
        glBindTexture(self.gl_tgt, self.gl_id)

    def unbind(self):
        glBindTexture(self.gl_tgt, 0)

    def unbindAndDisable(self):
        glBindTexture(self.gl_tgt, 0)
        glDisable(self.gl_tgt)

    def __del__(self):
        self.destroy()

    # retain a reference to these objects so we can use them during GC
    # cleanup
    def destroy(self, c_uint=c_uint, glDeleteTextures=glDeleteTextures,
            byref=byref, glDeleteRenderbuffersEXT=glDeleteRenderbuffersEXT):
        if self.gl_id == 0: return
        gl_id = c_uint(self.gl_id)
        if self.is_texture:
            glDeleteTextures(1, byref(gl_id))
        else:
            glDeleteRenderbuffersEXT(1, byref(gl_id))
        self.gl_id = 0

    def init(self, w = 0, h = 0, d = 0):
        if self.gl_id > 0: raise self.Failed('already initialised')

        if self.surface_type == self.SURF_NONE: return 0
        if self.surface_type == self.SURF_COLOUR and not self.is_texture:
            raise Failed('bad surface')
        if self.surface_type == self.SURF_STENCIL and self.is_texture:
            raise Failed('bad surface')

        gl_id = c_uint(0)

        if self.is_texture:
            if self.gl_tgt not in (GL_TEXTURE_RECTANGLE_ARB,):
                def _ceil_p2(x):
                    if x == 0: return 0
                    y = 1
                    while y < x: y = y * 2
                    return y

                w, h, d = _ceil_p2(w), _ceil_p2(h), _ceil_p2(d)

            glGenTextures(1, byref(gl_id))
            glBindTexture(self.gl_tgt, gl_id.value)

            glGetError()
            fmt = GL_RGBA
            if self.gl_fmt in (
                GL_DEPTH_COMPONENT16_ARB,
                GL_DEPTH_COMPONENT24_ARB,
                GL_DEPTH_COMPONENT32_ARB,
                GL_TEXTURE_DEPTH_SIZE_ARB,
                GL_DEPTH_TEXTURE_MODE_ARB):
                fmt = GL_DEPTH_COMPONENT

            if self.gl_tgt == GL_TEXTURE_1D:
                print >> sys.stderr, gl_id.value, '=> T(%d)' % (w,)
                glTexImage1D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w,
                             0,
                             fmt, GL_BYTE, None)
            elif self.gl_tgt in (GL_TEXTURE_2D, GL_TEXTURE_RECTANGLE_ARB):
                print >> sys.stderr, gl_id.value, '=> T(%d,%d)' % (w,h)
                glTexImage2D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w, h,
                             0,
                             fmt, GL_BYTE, None)
            elif self.gl_tgt == GL_TEXTURE_CUBE_MAP_EXT:
                print >> sys.stderr, gl_id.value, '=> C(%d,%d)' % (w,h)
                for i in range(6):
                    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i,
                                 0,
                                 self.gl_fmt,
                                 w, h,
                                 0,
                                 fmt, GL_BYTE, None)
            elif self.gl_tgt == GL_TEXTURE_3D:
                print >> sys.stderr, gl_id.value, '=> T(%d,%d,%d)' % (w,h,d)
                glTexImage3D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w, h, d,
                             0,
                             fmt, GL_BYTE, None)
            else:
                raise Failed('unhandled texture target: ' + hex(self.gl_tgt))
            err = glGetError()
            if err:
                raise Failed('failed to create texture: ' + hex(err))

            if self.gl_tgt == GL_TEXTURE_CUBE_MAP_EXT:
                for i in range(6):
                    if self.is_mipmapped:
                        glGenerateMipmapEXT(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i)
                    self.params.applyToCurrentTexture(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i)
                else:
                    if self.is_mipmapped:
                        glGenerateMipmapEXT(self.gl_tgt)
                    self.params.applyToCurrentTexture(self.gl_tgt)

            self.params.applyToCurrentTexture(self.gl_tgt)

            glBindTexture(self.gl_tgt, 0)
        else:
            print >> sys.stderr, gl_id.value, '=> R(%d,%d)' % (w,h)
            glGenRenderbuffersEXT(1, byref(gl_id))
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, gl_id)
            glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT, self.gl_fmt, w, h)
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, 0)

        if gl_id.value == 0:
            raise Failed('failed to init. glGetError(): ' + str(glGetError()))

        self.gl_id = gl_id.value
        self.width, self.height, self.depth = w, h, d



class FrameBuffer(object):
    bound_fbo = [ 0 ]

    def __init__(self, w, h, *surf):
        self.frame_buffer = 0
        self.width = w
        self.height = h

        self.colour = []
        self.depth = None
        self.stencil = None

        for s in surf: self.add(s)

    def add(self, surf):
        if type(surf) in (tuple, list):
            surf, gl_tgt = surf
        else:
            surf, gl_tgt = surf, surf.gl_tgt

        if not (gl_tgt in (GL_TEXTURE_2D, GL_TEXTURE_RECTANGLE_ARB, GL_RENDERBUFFER_EXT) or
                GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT <= gl_tgt < GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + 6):
            raise Failed('invalid target: ' + hex(gl_tgt))

        if   surf.surface_type == Surface.SURF_COLOUR:
            self.colour.append((surf, gl_tgt))
        elif surf.surface_type == Surface.SURF_DEPTH:
            self.depth = (surf, gl_tgt)
        elif surf.surface_type == Surface.SURF_STENCIL:
            self.stencil = (surf, gl_tgt)
        elif surf.surface_type == Surface.SURF_DEPTH:
            self.depth = (surf, gl_tgt)
        elif surf.surface_type == Surface.SURF_DEPTH_STENCIL:
            self.depth = self.stencil = (surf, gl_tgt)

    def init(self):
        for i in self.colour:
            i[0].init(self.width, self.height)
        if self.depth is not None:
            self.depth[0].init(self.width, self.height)
        if self.stencil is not None:
            self.stencil[0].init(self.width, self.height)

        fbo = c_uint(0)
        glGenFramebuffersEXT(1, byref(fbo))
        self.frame_buffer = fbo.value
        if self.frame_buffer == 0:
            raise Failed('failed to init. glGetError(): ' + str(glGetError()))

    def attach(self, mipmap_level = 0):
        if self.frame_buffer == 0:
            raise Failed('not initialised')

        self.bind()

        R = zip(self.colour, range(GL_COLOR_ATTACHMENT0_EXT,
            GL_COLOR_ATTACHMENT0_EXT + len(self.colour)))
        R.extend(((self.depth, GL_DEPTH_ATTACHMENT_EXT),
            (self.stencil, GL_STENCIL_ATTACHMENT_EXT)))

        for surf_info, attachment in R:
            if surf_info is None: continue
            surf, tgt = surf_info

            if surf.gl_id == 0: continue

            if surf.is_texture:
                print >> sys.stderr, 'ATTACH: T:%d' % (surf.gl_id,)
                glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,
                    attachment, tgt, surf.gl_id, mipmap_level)
            else:
                print >> sys.stderr, 'ATTACH: R:%d' % (surf.gl_id,)
                glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,
                    attachment, tgt, surf.gl_id)

        status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)

        if status != GL_FRAMEBUFFER_COMPLETE_EXT:
            raise Failed('attach failed: ' + hex(status))

    def pushBind(self):
        _bind  = FrameBuffer.bound_fbo[-1] != self.frame_buffer
        FrameBuffer.bound_fbo.append(self.frame_buffer)
        if _bind:
            glFlush()
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frame_buffer)

    @classmethod
    def popBind(cls):
        if len(FrameBuffer.bound_fbo) > 1:
            fbo = FrameBuffer.bound_fbo.pop()
            if fbo != FrameBuffer.bound_fbo[-1]:
                glFlush()
                glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,
                    FrameBuffer.bound_fbo[-1])

    def bind(self):
        if len(FrameBuffer.bound_fbo) == 1:
            return self.pushBind()

        if FrameBuffer.bound_fbo[-1] != self.frame_buffer:
            glFlush()
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frame_buffer)
            FrameBuffer.bound_fbo[-1] = self.frame_buffer

    unbind = popBind

    def colourBuffer(self, i):
        try:
            return self.colour[i][0]
        except:
            return None

    def depthBuffer(self):
        try:
            return self.depth[0]
        except:
            return None

    def stencilBuffer(self):
        try:
            return self.stencil[0]
        except:
            return None

    def __del__(self):
        self.destroy()

    # retain a reference to these objects so we can use them during GC
    # cleanup
    def destroy(self, c_uint=c_uint, byref=byref,
            glDeleteFramebuffersEXT=glDeleteFramebuffersEXT):
        if self.frame_buffer == 0: return
        self.colour = []
        self.depth = None
        self.stencil = None
        if self.frame_buffer != 0:
            fbo = c_uint(self.frame_buffer)
            glDeleteFramebuffersEXT(1, byref(fbo))
        self.frame_buffer = 0


def setup2D(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w, 0, h, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()



class FallingSandSupportFunctionsShader(FragmentShader):
    def __init__(self):
        FragmentShader.__init__(self, "falling_sand_support_functions_rect_f", """\
bool isLiquid(vec4 color){
//    vec4 current = texture2DRect(src, xy);                                                                       //oil(0.50, 0.25, 0.25)
return all(equal(color.rgb, vec3(0.0))) || all(equal(color.rgb, vec3(0.0, 0.0, 1.0))) ||
                           //oil(0.50, 0.25, 0.25)
    (    all(greaterThan(color.rgb, vec3(0.49, 0.24, 0.24))) && all(lessThan(color.rgb, vec3(0.51, 0.26, 0.26)))   );
}
""")


class FallingSandShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("babs_rect_f", """\

uniform sampler2DRect rand;        
uniform sampler2DRect src;

uniform float randomOffset;

void main() {

        vec3 bottomSand = vec3(0.5, 0.5, 0.5);
        vec3 topSand = vec3(0.6, 0.6, 0.6);
	vec4 current = texture2DRect(src, gl_TexCoord[0].st);

	vec4 above = texture2DRect(src, gl_TexCoord[0].st + vec2(0.0, 1.0));
        vec4 below = texture2DRect(src, gl_TexCoord[0].st + vec2(0.0, -1.0));



        vec4 twoLeft = texture2DRect(src, gl_TexCoord[0].st + vec2(-2.0, 0.0));

        vec4 left = texture2DRect(src, gl_TexCoord[0].st + vec2(-1.0, 0.0));
        vec4 right = texture2DRect(src, gl_TexCoord[0].st + vec2(1.0, 0.0));

        vec4 lowerLeft = texture2DRect(src, gl_TexCoord[0].st + vec2(-1.0, -1.0));
        vec4 lowerRight = texture2DRect(src, gl_TexCoord[0].st + vec2(1.0, -1.0));
        vec4 upperLeft = texture2DRect(src, gl_TexCoord[0].st + vec2(-1.0, 1.0));
        vec4 upperRight = texture2DRect(src, gl_TexCoord[0].st + vec2(1.0, 1.0));
        

        vec4 randNum = texture2DRect(rand, gl_TexCoord[0].st + vec2(randomOffset, randomOffset));
        vec4 rightRandNum = texture2DRect(rand, gl_TexCoord[0].st + vec2(randomOffset + 1.0, randomOffset));
        vec4 leftRandNum = texture2DRect(rand, gl_TexCoord[0].st + vec2(randomOffset - 1.0, randomOffset));
        vec4 belowRandNum = texture2DRect(rand, gl_TexCoord[0].st + vec2(randomOffset, randomOffset - 1.0));                
        
        vec3 red = vec3(1.0, 0.0, 0.0);

        int xOdd = int(mod(gl_TexCoord[0].s, 2.0));
        int yOdd = int(mod(gl_TexCoord[0].t, 2.0));


        //red doesn't spread to white or blue
        if( (all(equal(above.rgb, red)) || all(equal(below.rgb, red)) || all(equal(left.rgb, red)) || all(equal(right.rgb, red))) && (any(notEqual(current.rgb, vec3(1.0))) &&  any(notEqual(current.rgb, vec3(0.0, 0.0, 1.0)))) ){
            if(all(greaterThan(current.rgb, bottomSand)) && all(lessThan(current.rgb, topSand)) && (xOdd == 0) && (yOdd == 0)){
                gl_FragColor = current;
            }
            else{
                gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
            }
        }
        else{

//begin down movement
            if(isLiquid(current) && !(isLiquid(below)) &&
               (belowRandNum.r > 0.2) &&
               (all(lessThan(below.rgb, bottomSand)) || all(greaterThan(below.rgb, topSand)))
                    // not sand
               ){ //black
     	   	    gl_FragColor = vec4(1.0); //black becoming white
            }
	    else if(!isLiquid(current) && ( all(lessThan(current.rgb, bottomSand)) || all(greaterThan(current.rgb, topSand)) ) //notsand
                    && (randNum.r > 0.2)
                    && isLiquid(above) ){ //black
  	   	    gl_FragColor = above; //white becoming black
	    }
//end down movement
            // sideways movement
//begin right sideways movement

            else if( isLiquid(left) && all(equal(current.rgb, vec3(1.0))) &&
//               (leftRandNum.r > 0.1) &&
                 leftRandNum.r > 0.5 && //make sure pixel doesn't go both left and right               
               !(
                   isLiquid(above) || 
                   all(equal(lowerLeft.rgb, vec3(1.0)))
               )

            ){ 
                gl_FragColor = left; //white becoming black
            }
           else if( all(equal(right.rgb, vec3(1.0))) && isLiquid(current) &&
//               (randNum.r > 0.1) &&
                 randNum.r > 0.5 && //make sure pixel doesn't go both left and right


               !(
                  all(equal(below.rgb, vec3(1.0)))  || //current should fall but randomly isn't
                 //right above not going to fall
                  isLiquid(upperRight)
               )
            ){
                gl_FragColor = vec4(1.0); //black becoming white
            }
//end right sideways movement
//begin left sideways movement
            else if( isLiquid(right) && all(equal(current.rgb, vec3(1.0))) &&
//               (leftRandNum.r > 0.1) &&
                 rightRandNum.r < 0.5 && //make sure pixel doesn't go both left and right
                 !isLiquid(left) && //make you don't move left into same pixel as someone moving right
               !(
                   isLiquid(above) || 
                   all(equal(lowerRight.rgb, vec3(1.0)))
               )
            ){ 
                gl_FragColor = right; //white becoming black
            }

           else if( all(equal(left.rgb, vec3(1.0))) && isLiquid(current) &&
//               (randNum.r > 0.1) &&
                 randNum.r < 0.5 && //make sure pixel doesn't go both left and right
                 !isLiquid(twoLeft) && //make you don't move left into same pixel as someone moving right                 
               !(
                  all(equal(below.rgb, vec3(1.0)))|| //current should fall but randomly isn't
                 //right above not going to fall
                  isLiquid(upperLeft)
               )
            ){
                gl_FragColor = vec4(1.0); //black becoming white
            }
//end left sideways movement
            else{
                gl_FragColor = current;
            }
    }

    //turn red back to white randomly
    if(all(equal(current.rgb, red)) && randNum.r < 0.10){
        gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
    }

}
""").addDependency(FallingSandSupportFunctionsShader()))



class SparseShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("babs_rect_f", """\
uniform sampler2DRect src;
void main() {
        vec4 current = texture2DRect(src, vec2(gl_TexCoord[0].s + 100.0, gl_TexCoord[0].t + 100.0));

        if(current.r > 0.5)
             gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
         else
             gl_FragColor = gl_Color;

}
"""))



def calcRectCenter(l,t,r,b):#,v=()):
    """ returns rect center point -> x,y
        calcRectCenter(l,t,r,b)
    """
##    if len(v) : l,t,r,b = v[0],v[1],v[2],v[3]
    return l+((r-l)*0.5), t+((b-t)*0.5)



def calcPolygonRect(pointArray):
    """ receives a point list and returns the rect that contains them as a tupple -> tuple left, top, right, bottom
    """
    # init to ridiculously big values. not very elegant or eficient
    l, t, r, b = 10000000, 10000000, -10000000, -10000000

    for n in pointArray: # calc bounding rectangle rect
        if n[0] < l : l = n[0]
        if n[0] > r : r = n[0]
        if n[1] < t : t = n[1]
        if n[1] > b : b = n[1]

    return l, t, r, b


    
class Polygon():
    def __init__(self, vertices, color=(0,0,0,1)):
        self.vertices = vertices
        self.color = color

    def render(self):
         x, y = calcRectCenter(*calcPolygonRect(self.vertices))
         self.drawVertex(x, y, 0, [(i[0] - x, i[1] - y) for i in self.vertices], self.color)

    def drawVertex(self, x, y,  z=0, v=(), color=(0,0,0,1), stroke=0, rotation=0.0,   style=0):
        glColor4f(*self.color)    
        glPushMatrix()
        glTranslatef(x, y, -0)
        glBegin(GL_QUADS)
        for p in v:
            glTexCoord2f(p[0], p[1], 0); glVertex3f(p[0], p[1],0)  # draw each vertex

        glEnd()
        # -- end drawing
        glPopMatrix()
        

class SandWindow(pyglet.window.Window):

    pen = None
    color = (1.0, 1.0, 1.0, 1.0)
    penSize = 50


    def __init__(self, width, height):
        super(SandWindow, self).__init__(width, height, resizable=True)
        self.screen_width = width
        self.screen_height = height
        self.initFrameBuffers(0.0)
        



    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT:
            self.pen = Polygon([( x, y), (x, self.penSize + y), (x + self.penSize, y + self.penSize), (self.penSize + x, y) ],color=self.color)
        if buttons & mouse.RIGHT:
            self.pen  = Circle(x,y,width=100,color=(1.0, 1.0, 1.0, 1.0))


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            self.pen = Polygon([( x, y), (x, self.penSize + y), (x + self.penSize, y + self.penSize), (self.penSize + x, y) ],color=self.color)            
        if buttons & mouse.RIGHT:
            self.pen  = Circle(x,y,width=100,color=(1.0, 1.0, 1.0, 1.0))            




    def on_key_press(self, symbol, modifiers):
        if symbol == key.C:
            self.pen = "clear"
        if symbol == key._1:
            self.color = (1.0, 0.0, 0.0, 1.0)
        if symbol == key._2:
            self.color = (0.0, 1.0, 0.0, 1.0)            
        if symbol == key._3:
            self.color = (0.0, 0.0, 1.0, 1.0)
        if symbol == key._4:
            self.color = (1.0, 1.0, 1.0, 1.0)
        if symbol == key._5:
            self.color = (0.0, 0.0, 0.0, 1.0)
        if symbol == key._6: #sand brown
            self.color = (0.55, 0.55, 0.55, 1.0)
        if symbol == key._7: 
            self.color = (0.5, 0.25, 0.25, 1.0)
            
            
            
    def drawPen(self):
        if self.pen is None:
            return
        elif self.pen == "clear":
            glClearColor(1.0, 1.0, 1.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        else:
            self.pen.render()
            self.pen = None


    def on_resize(self, screen_width, screen_height):
        print("res", screen_width, screen_height)
        self.screen_width = screen_width
        self.screen_height = screen_height
        pyglet.clock.unschedule(window.initFrameBuffers)
        pyglet.clock.schedule_once(window.initFrameBuffers, 1.0)
        

    def initFrameBuffers(self, dt):
        self.renderToBuffer = createFrameBufferObject(self.screen_width, self.screen_height)
        self.inputBuffer = createFrameBufferObject(self.screen_width, self.screen_height)
        self.randomFbo = createFrameBufferObject(self.screen_width, self.screen_height)
        fillFboWithRandomData(self.randomFbo, self.screen_width, self.screen_height)
        self.fallingSandShader = FallingSandShader()
        self.sparseShader = SparseShader()
        glDisable(GL_DEPTH_TEST)        



    def update(self, dt):
        print("up")
        global i

#    global player
#    global womanScream

        self.renderToBuffer, self.inputBuffer = self.inputBuffer, self.renderToBuffer
#draw spray paint patter cursor
        self.inputBuffer.bind()
        self.sparseShader.install()
        glEnable(self.inputBuffer.colourBuffer(0).gl_tgt)
        self.sparseShader.usetTex("src", 0, self.randomFbo.colourBuffer(0))
        window.drawPen()
        self.sparseShader.uninstall()
        glDisable(self.inputBuffer.colourBuffer(0).gl_tgt)
        self.inputBuffer.unbind()


        glActiveTexture(GL_TEXTURE0)
#calculate next screens state
        randomOffset = random.randint(0, 100)
        self.renderToBuffer.bind()
        self.fallingSandShader.install()
        glEnable(self.inputBuffer.colourBuffer(0).gl_tgt)
        self.fallingSandShader.usetTex("src", 0, self.inputBuffer.colourBuffer(0))                
        self.fallingSandShader.usetTex("rand", 1, self.randomFbo.colourBuffer(0))
        self.fallingSandShader.uset1F("randomOffset", randomOffset)
        setup2D(self.screen_width, self.screen_height)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
        glTexCoord2f( self.screen_width, 0.0); glVertex2f( self.screen_width, 0.0)
        glTexCoord2f( self.screen_width,  self.screen_height); glVertex2f( self.screen_width,  self.screen_height)
        glTexCoord2f(0.0,  self.screen_height); glVertex2f(0.0,  self.screen_height)
        glEnd()
        glDisable(self.inputBuffer.colourBuffer(0).gl_tgt)
        glDisable(self.randomFbo.colourBuffer(0).gl_tgt)
        self.fallingSandShader.uninstall()
        self.renderToBuffer.unbind()
        glActiveTexture(GL_TEXTURE0)


#display current state to screen


        glBindTexture(self.renderToBuffer.colourBuffer(0).gl_tgt, self.renderToBuffer.colourBuffer(0).gl_id)
        setup2D(self.screen_width, self.screen_height)
        glColor4f(*(1, 1, 1, 1))
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
        glTexCoord2f( self.screen_width, 0.0); glVertex2f( self.screen_width, 0.0)
        glTexCoord2f( self.screen_width,  self.screen_height); glVertex2f( self.screen_width,  self.screen_height)
        glTexCoord2f(0.0,  self.screen_height); glVertex2f(0.0,  self.screen_height)
        glEnd()


        glBindTexture(self.renderToBuffer.colourBuffer(0).gl_tgt, 0)
        glBindTexture(self.inputBuffer.colourBuffer(0).gl_tgt, 0)
        glDisable(self.inputBuffer.colourBuffer(0).gl_tgt)
        glDisable(self.randomFbo.colourBuffer(0).gl_tgt)        
        glActiveTexture(GL_TEXTURE0)

        pyglui.draw_gui()

        i += 1
            


        
def createFrameBufferObject(screen_width, screen_height):

    cparams = TextureParam(wrap = GL_CLAMP, filter=GL_NEAREST)

    buf = FrameBuffer(screen_width, screen_height,
        Surface(Surface.SURF_COLOUR, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            params=cparams),
        Surface(Surface.SURF_DEPTH, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            gl_fmt=GL_DEPTH_COMPONENT32_ARB, is_texture=True,
            is_mipmapped=False, params=cparams))
    buf.init()
    buf.attach()
    buf.unbind()
    return buf


def fillFboWithRandomData(randomFbo, screen_width, screen_height):
    randomImage = pyglet.image.SolidColorImagePattern(color=(0,0,50,255)).create_image(screen_width,screen_height)
    data = randomImage.get_data('RGB', randomImage.pitch)

    newData = (''.join(["%c%c%c%c" % ((random.randint(0, 255),)*4) for i in xrange((len(data)/4)/4)] ) *4)

    randomImage.set_data('RGB', randomImage.pitch, newData)
    texture = randomImage.get_texture(True)

    randomFbo.bind()
    glEnable(texture.target)
    glBindTexture(texture.target, texture.id)
    setup2D(screen_width, screen_height)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
    glTexCoord2f( screen_width, 0.0); glVertex2f( screen_width, 0.0)
    glTexCoord2f( screen_width,  screen_height); glVertex2f( screen_width,  screen_height)
    glTexCoord2f(0.0,  screen_height); glVertex2f(0.0,  screen_height)
    glEnd()
    glDisable(texture.target)
    randomFbo.unbind()


    
def drawStaticSprinkers(dt, screen_width, screen_height):
    sprinklerSize = 10

    renderToBuffer.bind()
    sparseShader.install()
    glEnable(renderToBuffer.colourBuffer(0).gl_tgt)
    sparseShader.usetTex("src", 0, randomFbo.colourBuffer(0))

    x_anchors = [ int((screen_width - 30)*(i/3.0)) for i in range(1,4)][::-1]
    x,y = x_anchors[0],(screen_height - sprinklerSize)
    waterSprinkler = Polygon([( x, y), (x, sprinklerSize + y), (x + sprinklerSize, y + sprinklerSize), (sprinklerSize + x, y) ],color=(0,0,0,1))
    x = x_anchors[1]
    sandSprinkler =  Polygon([( x, y), (x, sprinklerSize + y), (x + sprinklerSize, y + sprinklerSize), (sprinklerSize + x, y) ],color=(0,0,0,1))    

    x = x_anchors[2]
    oilSprinkler =   Polygon([( x, y), (x, sprinklerSize + y), (x + sprinklerSize, y + sprinklerSize), (sprinklerSize + x, y) ],color=(0,0,0,1))


    waterSprinkler.render()
    sandSprinkler.render()    
    oilSprinkler.render()

    sparseShader.uninstall()
    glDisable(renderToBuffer.colourBuffer(0).gl_tgt)
    renderToBuffer.unbind()




#womanScream = pyglet.media.load("woman_scream.wav", streaming=False)
#player = pyglet.media.Player()
#player.queue(womanScream)

screen_width = 251
screen_height = 251

window = SandWindow(screen_width, screen_height)



def redToOne():
    window.dispatch_event("on_key_press", key._1, [])
def greenToTwo():
    window.dispatch_event("on_key_press", key._2, [])
def blueToThree():
    window.dispatch_event("on_key_press", key._3, [])
def whiteToFour():
    window.dispatch_event("on_key_press", key._4, [])
def blackToFive():
    window.dispatch_event("on_key_press", key._5, [])
def greyToSix():
    window.dispatch_event("on_key_press", key._6, [])
def sandBrownToSix():
    window.dispatch_event("on_key_press", key._7, [])
def adjustPenSize(position):
    window.penSize = 50 * position



card = pyglui.Card([
    widget.ImageButton(image.SolidColorImagePattern(color=(0, 0, 0, 255)).create_image(20,20), 0, 0, blackToFive),
    widget.ImageButton(image.SolidColorImagePattern(color=(255, 255, 255, 255)).create_image(20,20), 20, 0, whiteToFour),
    widget.ImageButton(image.SolidColorImagePattern(color=(0, 0, 255, 255)).create_image(20,20), 40, 0, blueToThree),
    widget.ImageButton(image.SolidColorImagePattern(color=(0, 255, 0, 255)).create_image(20,20), 60, 0, greenToTwo),
    widget.ImageButton(image.SolidColorImagePattern(color=(255, 0, 0, 255)).create_image(20,20), 80, 0, redToOne),
    widget.ImageButton(image.SolidColorImagePattern(color=(140, 140, 140, 255)).create_image(20,20), 100, 0, greyToSix),
    widget.ImageButton(image.SolidColorImagePattern(color=(127, 63, 63, 255)).create_image(20,20), 120, 0, sandBrownToSix),
    widget.Slider(160, 10, adjustPenSize, position=0.0, width=100.0, size=20)
    ])
pyglui.init(window, card)



#player.play()

i = 0
pyglet.clock.schedule_interval(window.update, 1.0/120.0)
#pyglet.clock.schedule_interval(drawStaticSprinkers, 1.0/20.0, screen_width, screen_height)
pyglet.app.run()



