import os			      # command to deal with files / folders 
import pygame                 	      # main pygame library
from pygame.locals import *           # subfunctions in pygame
import logging	                      # logging to file 
from dataframe import DataFrame       # class to store data
import argparse			      # class to parse arguments
import time,sys,datetime,math,random  # 
import numpy as np                    # commment this if not working

import expconf
from patchgenerator import *
from statelogic import Trial,UserAction    #LB not working 

# Main loop for the experiment
# ============================
def startExp(recover, skipInstr):
  """this function is called when the program starts.
    it initializes everything it needs, then runs in
    a loop until the function returns."""

  # Initialize Everything
  # =====================
  pygame.init()

  # -- for full screen -- set full screen in ini file---
  if (expconf.cf.getint('main','fullscreen')):
    modes  = pygame.display.list_modes(0)
    if ((1280,800) in modes):
      screen = pygame.display.set_mode((1280,800), pygame.FULLSCREEN, 16)
    else:
      screen = pygame.display.set_mode(modes[0], pygame.FULLSCREEN, 16)
  else:
    screen = pygame.display.set_mode((800, 600))     # creates a window of this size

  expconf.cf.set('game','screenwidth',screen.get_rect().w)

  pygame.display.set_caption('Patch-foraging game')
  pygame.mouse.set_visible(0)

  #Create The Backgound
  background = pygame.Surface(screen.get_size())
  background = background.convert()
  background.fill((216, 216, 208))                 # setting grey background

  #Put Text On The Background, Centered
  if pygame.font:
    font    = pygame.font.Font(None, 36)
    text    = font.render("", 1 , (10, 10, 10))
    textpos = text.get_rect(centerx=background.get_width()/2)
    background.blit(text, textpos)                 # draw (here it draws text to background)

  #Display The Background
  screen.blit(background, (0, 0))                  # add background to screen that does not yet appear on the computer
  pygame.display.flip()                            # flip applies to screen we see

  #Prepare Game Objects
  clock     = pygame.time.Clock()
  user      = UserAction()

  # grouping the sprites in the Trial
  trial = Trial(user,screen,background,recover, skipInstr)

  # Main Loop
  # ===========
  while 1:                                         # this is done continuously (every 30 ms) state is checked 
    clock.tick(45)                                 # and we update to the screen

    # Handle Input Events
    # -------------------
    for event in pygame.event.get():
      if event.type == QUIT:
        return
 
      # keypress down, choice is made
      if event.type == KEYDOWN:                      # if a key is pressed
        if (event.key==K_RIGHT):
          user.foreaging = UserAction.STATE_EXIT     # update user action whenever pressed but only react in wait for decision
          logging.info('[key][exit][' + str(float(pygame.time.get_ticks())/1000) + ']')
        elif (event.key==K_DOWN):  
          user.foreaging = UserAction.STATE_STAY     # update user action
          logging.info('[key][stay][' + str(float(pygame.time.get_ticks())/1000) + ']')
      
        # if ((event.key==K_p)|
        #            (event.key==K_o)|
        #            (event.key==K_i)|
        #            (event.key==K_u)|
        #            (event.key==K_SEMICOLON)|
        #            (event.key==K_l)|
        #            (event.key==K_k)|
        #            (event.key== K_j)):     # K_p K_RIGHT and it is RIGHTARROW then exit the patch
        #          user.foreaging = UserAction.STATE_EXIT     # update user action whenever pressed but only react in wait for decision
        #          logging.info('[key][exit][' + str(float(pygame.time.get_ticks())/1000) + ']')
        #        elif ((event.key==K_q)|    
        #              (event.key==K_w)|
        #              (event.key==K_e)|
        #              (event.key==K_r)|
        #              (event.key==K_a)|
        #              (event.key==K_s)|
        #              (event.key==K_d)|
        #              (event.key== K_f)):                    # K_q K_DOWN and it is DOWNARROW then continue in the patch
        #          user.foreaging = UserAction.STATE_STAY     # update user action
        #          logging.info('[key][stay][' + str(float(pygame.time.get_ticks())/1000) + ']')
        elif event.key == K_SPACE:                   # and it is DOWNARROW then continue in the patch
          user.foreaging = UserAction.STATE_SPACEBAR # update user action
        elif event.key == K_LEFT:                    # and it is DOWNARROW then continue in the patch
          user.foreaging = UserAction.STATE_LEFT     # update user action
                                                     
      if event.type == KEYUP:                        # this is when a key is released
        if ((event.key==K_q)|
            (event.key==K_w)|
            (event.key==K_e)|
            (event.key==K_r)|
            (event.key==K_a)|
            (event.key==K_s)|
            (event.key==K_d)|
            (event.key== K_f)):                         # K_q K_DOWN                        
          user.foreaging = UserAction.STATE_NONE
        if ((event.key==K_p)|
            (event.key==K_o)|
            (event.key==K_i)|
            (event.key==K_u)|
            (event.key==K_SEMICOLON)|
            (event.key==K_l)|
            (event.key==K_k)|
            (event.key== K_j)):      # K_RIGHT
          user.foreaging = UserAction.STATE_NONE
        if event.key == K_SPACE:
          user.foreaging = UserAction.STATE_NONE
        elif event.key == K_LEFT:                    # and it is DOWNARROW then continue in the patch
          user.foreaging = UserAction.STATE_NONE     # update user action
        elif event.key == K_ESCAPE and pygame.key.get_mods()&pygame.KMOD_LSHIFT:
          return

    trial.update()                                  # update all sprites in trial

    #Draw Everything
    screen.blit(background, (0, 0))                 # in every loop redraw background and sprites
    trial.draw(screen)                              # screen.blit of each sprite
    pygame.display.flip()

  # Game Over
  # =========

def parseColor(s):
  v = s.rsplit(',')
  return((int(v[0]),int(v[1]),int(v[2])))

