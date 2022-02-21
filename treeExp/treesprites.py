import os, pygame
from pygame.locals import *
import pygame.gfxdraw
import logging
import random, math
import ConfigParser
# IMPORTING MODULES

if not pygame.font:                       
  print ('Warning, fonts disabled') #LB added parentheses 
if not pygame.mixer: 
  print ('Warning, sound disabled')


# FUNCTIONS
# =========

# to load images
# --------------
def load_image(name, colorkey=None):     # only sprites load images
  fullname = os.path.join('.', name)
  try:
    image = pygame.image.load(fullname)
  except pygame.error, message:
    print 'Cannot load image:', fullname
    raise SystemExit, message
  #image = image.convert()
  if colorkey is not None:
    if colorkey is -1:
      colorkey = image.get_at((0,0))
    image.set_colorkey(colorkey, RLEACCEL)
  image.convert()
  return image, image.get_rect()


# to load sounds
# --------------
def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer:
        return NoneSound()
    try:
        sound = pygame.mixer.Sound(name)
    except pygame.error, message:
        print 'Cannot load sound:', wav
        raise SystemExit, message
    return sound

# to make background transparent
# ------------------------------
def makeBGTransparent(img):
  # get all border values to make the background transparent by making every pixel with 
  # same color as upper left corner transparent
  for i in range(0,img.get_rect().w):
    img.set_colorkey(img.get_at((i,0)),pygame.RLEACCEL)
  return(img)

# CLASS TREE 
# ==========
# it will have a method to regenerate itself
class Tree(pygame.sprite.Sprite):
  def __init__(self,pos):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    
    # create the random tree
    self.pos_center = pos
    self.pos = pos 
    self.diameter = 100
    self.isShaking = 0
    self.reset()
  
  # regenerates the tree
  def reset(self):
    self.image = pygame.Surface((400,400))           # background of the image
    self.image.set_colorkey((0,0,0))                 # background set to be transparent, any black pixel is transparent
    self.rect  = self.image.get_rect()               # right now at upper L corner 

    # creating the tree trunk
    r   = self.rect.copy()                           # create new rect
    r.w = 20                                         # thinner width
    r.h = r.h/2                                      # half of created surface
    r.midbottom = self.rect.midbottom                # pos of trunk inside surface of tree 
  
    pygame.gfxdraw.box(self.image,r,(80,39,18))       # module of pygame (nice drawing)
  
    cred = 20
    # cred = random.randrange(0,100)  # common to all leafs
    # randomly draw green circles in x,y
    for i in range(1,200):
      # we draw randomly the color and the position
      x = self.diameter
      y = self.diameter
      while (x**2 + y**2 > (self.diameter)**2):      # check x^2 + y^2 < self.diameter^2
        x = int(random.gauss(0,0.08)*self.rect.w)    # draw where to position center of the circle in x and y
        y = int(random.gauss(0,0.1)*self.rect.h)

      cblue    = random.randrange(150,250)
      # draw a circle at that point
      # pygame.draw.circle(self.image, (25,25,25), (self.rect.centerx + x,self.rect.centery + y), 15)
      pygame.gfxdraw.filled_circle(self.image, self.rect.centerx + x, -int(self.rect.h/8) + self.rect.centery + y, 15, (cred,cblue,0))
  
  # when moving the tree, say at what percentage we are
  # from behing at the next tree
  def setPosition(self,percent,width):
    # the total length to go through
    D = width + 2*self.diameter
    # the distance we must have gone through already
    if (percent<0.5):
      xdev = - percent * D # absolute deviation from the center, update every 45 ms
    else:
      xdev = D - percent * D 

    self.pos = (int(self.pos_center[0] + xdev), self.pos[1])
    #logging.info("tree is at " + str(self.rect.centerx))

  def setAlpha(self,a):
    self.image.set_alpha(a)

  def update(self):
    self.rect.midbottom = self.pos                   # midbottom of the surface will be at position 
    if (self.isShaking):
      self.rect = self.rect.move(int(random.gauss(0,5)),0)

# CLASS APPLE
# ===========
class Apple(pygame.sprite.Sprite):
  def __init__(self,pos,portion,img='img/apple.png'):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance

    # load the apple image
    self.image , self.rect = load_image(img , -1)
    self.pos = pos # this is the random position that is created in trial

    #scaling it down
    r = self.image.get_rect()
    self.image = pygame.transform.scale(self.image, (r.w/5,r.h/5))
    self.image.set_colorkey(self.image.get_at((0,0))) #,pygame.RLEACCEL)  # sets the background to transparent
    self.rect = self.image.get_rect()

    # cutoff the apple by val
    if (portion<1):
      transparent_color = self.image.get_at((0,0))
      portion = portion/0.6 + 0.1
      r   = self.rect.copy()
      r   = r.move(int(portion * r.w/2),5)              # replace apple pixels with transparent, when portion 1 no cover apple
      #pygame.gfxdraw.filled_circle(self.image,r.centerx,r.centery,r.w/2,(0,0,0))  # blit filled circle onto the image
      pygame.draw.ellipse(self.image,transparent_color,r)

  def update(self):
    self.rect.midtop = self.pos        # position of the surface (load image so don't need to create one)

# Class to draw fixation cross
# ============================

class FixationCross(pygame.sprite.Sprite):
  def __init__(self,pos,shape='cross'):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    self.pos    = pos
    self.color  =(2,2,2)                  # default color is black
    self.shape = shape
    self.change()                         # call the function change to initialize the drawing
    self.active = 0

  def change(self):
    self.image = pygame.Surface((40,40))  # create background surface to draw on
    self.image.set_colorkey((0,0,0))
    self.rect = self.image.get_rect()

    if self.shape=='cross':
        r  = self.rect.copy()
        r.w      = 5                           # width of the cross
        r.center = self.rect.center            # center of the surface
        #pygame.gfxdraw.box(self.image,r,self.color)
        pygame.draw.rect(self.image,self.color,r)
        r  = self.rect.copy()
        r.h      = 5
        r.center = self.rect.center
        #pygame.gfxdraw.box(self.image,r,self.color)
        pygame.draw.rect(self.image,self.color,r)
    else:
        r  = self.rect.copy()
        pygame.draw.ellipse(self.image,self.color,r)

    self.update()

# Redraw if state changes
  def activate(self):
    if (self.active != 1):
      self.active = 1
      self.color = (255,255,255)               # white
      self.change()

  def deactivate(self):
    if (self.active != 0):
      self.active = 0
      self.color=(80,39,18)                    # brown
      self.change()

  def update(self):
    self.rect.midtop = self.pos

# Class ImageBox, to display instruction or other
# ===============================================
class ImageBox(pygame.sprite.Sprite):
  def __init__(self,imgPath,pos):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    # load the apple image
    self.image , self.rect = load_image('img/'+imgPath  , -1)
    self.pos = pos # this is the random position that is created in trial
    self.rect = self.image.get_rect()

  def update(self):
    self.rect.center = self.pos


# class to display irrelevant reward
# ==================================
class PoissonReward(pygame.sprite.Sprite):  
  def __init__(self,pos):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    self.pos = pos
    self.font = pygame.font.Font(None,80)
    self.setPReward(0)

  def update(self):
    self.rect.center = self.pos

  def setPReward(self,val):
    # create an empty image
    self.image = pygame.Surface((200,40))  # create background surface to draw on
    self.image.set_colorkey((0,0,0))
    self.rect = self.image.get_rect()

    #text = self.font.render(u"\u00A2" + str(int(val)), 1, (247,255,1)) # gold font -- but hard to see!
    text = self.font.render('You just gor awarded an extra ' + str(int(val*100)/100.0) + u"\u00A2", 1, (50,50,1))
    self.image = text


# Class to display the score
# ==========================
class Score(pygame.sprite.Sprite):
  def __init__(self,pos):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    self.pos = pos # this is the random position that is created in trial
    self.font = pygame.font.Font(None,80)
    self.setScore(0)

  def update(self):
    self.rect.center = self.pos

  def setScore(self,val):
    # create an empty image
    self.image = pygame.Surface((200,40))  # create background surface to draw on
    self.image.set_colorkey((0,0,0))
    self.rect = self.image.get_rect()

    #text = self.font.render(u"\u00A2" + str(int(val)), 1, (247,255,1)) # gold font -- but hard to see!
    text = self.font.render(str(int(val*100)/100.0) + u"\u00A2", 1, (50,50,1))
    self.image = text
    #self.image.blit(text,(0,0))

# Class to draw text on the screen
# ================================
class TextBox(pygame.sprite.Sprite):
  def __init__(self,pos):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    self.image = pygame.Surface((200,40))  # create background surface to draw on
    self.pos = pos
    self.rect = self.image.get_rect()
    self.col = (50,50,1)

  def setText(self,txt,bgcol=(0,0,0),size=55):
    # get more fonts from http://www.sitetoolcenter.com/download-free-fonts/page14.php
    font = pygame.font.Font('img/GARB.TTF',size)
    
    # find the number of lines
    lines = txt.rsplit('\n')
    
    # compute the height of a line
    w, h = font.size(lines[0]) 

    # get total heiht using a 10% padding
    H = int(1.1 * h * len(lines))
    
    # get max widths
    W=0
    for line in lines:
      w, h = font.size(line) 
      if (w > W):
        W=w

    # create the image
    self.image = pygame.Surface((W,H))  # create background surface to draw on
    self.image.fill(bgcol)
    self.image = self.image.convert()

    # blit each line correctly
    x,y = (0,0)
    for line in lines:
      w, h = font.size(line) 
      x = (W-w)/2
      text = font.render(line, 1, self.col)
      self.image.blit(text,(x,y))
      y = y + int(1.1*h)

    self.rect = self.image.get_rect()
    self.image.set_colorkey(bgcol)    
  # we are done!

  def update(self):
    self.rect.center = self.pos


# Class to draw text on the screen
# ================================
# this draws an arc that reprensents the
# money collected -- so we need a 
class Ticker(pygame.sprite.Sprite):
  def __init__(self,pos,speed2=1):
    pygame.sprite.Sprite.__init__(self) # call Sprite initializer for every sprite instance
    self.image = pygame.Surface((200,100))  # create background surface to draw on
    self.pos = pos
    self.rect = self.image.get_rect()
    self.col = (50,50,150)
    self.angle = 0
    self.text = '0'
    self.bgcol = (0,0,0)
    self.speed2 = speed2

  def setAngle(self,angle):
    self.angle = float(angle-90)/360 * 2*math.pi

  def setCount(self,count,bgcol=(0,0,0)):
    # get more fonts from http://www.sitetoolcenter.com/download-free-fonts/page14.php
    self.text = '' + str(float(int(count*100))/100)
    self.bgcol = bgcol

  def update(self):
    # we want to raw a pie, to do that we 
    # are going to draw a rectangle
    # and rotate it
    self.image = pygame.Surface((200,100))  # create background surface to draw on
    self.image.fill(self.bgcol)
    self.image = self.image.convert()
 
    font = pygame.font.Font('img/GARB.TTF',36)
    text = font.render(self.text, 1, (170,170,170))
    r = self.rect.copy().move(100,0)
    self.image.blit(text,r)

    r = self.rect.copy().move(-50,0)
    pygame.draw.circle(self.image,(120,120,120),r.center,self.rect.height/2)
    pygame.draw.circle(self.image,self.col,r.center, 10)
    
    # draw a first line
    spos = r.center
    eposx = r.centerx + int((self.rect.height-2)/3 * math.cos(self.angle))
    eposy = r.centery + int((self.rect.height-2)/3 * math.sin(self.angle))
    pygame.draw.line(self.image,self.col,spos,(eposx,eposy),3) 

    # and a second faste
    spos = r.center
    eposx = r.centerx + int((self.rect.height-2)/2 * math.cos(self.angle*self.speed2))
    eposy = r.centery + int((self.rect.height-2)/2 * math.sin(self.angle*self.speed2))
    pygame.draw.line(self.image,self.col,spos,(eposx,eposy),1) 





