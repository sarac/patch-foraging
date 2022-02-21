import os			      # command to deal with files / folders 
import pygame                 	      # main pygame library
from pygame.locals import *           # subfunctions in pygame
import logging	                      # logging to file 
from dataframe import DataFrame       # class to store data
import argparse			      # class to parse arguments
import time,sys,datetime,math,random  # 
import numpy as np                    # commment this if not working

import expconf     #THIS ONE WORKS 

class PatchGenerator:
  #  This class handles the logic of the patch, it returns
  #  the delay and reward. Need to tell it when to reset or 
  #  draw a new state
  def __init__(self):

    #self.bgcolors = list()
    # loading colors in random order
    #for i in range(1, expconf.cf.getint('game', 'ncolors') +1):
    #  self.bgcolors.append(parseColor(expconf.cf.get('game','color'+str(i)))) 
    #randomize affectation
    #random.shuffle(self.bgcolors)
    # store color sequence
    #expconf.cf.set('game', 'flipBgColor', self.flipBgColor)
    #print "color " , str(self.bgcolors[1])

    self.loadPatchBlock(0)
    self.reset()

  # METHOD: switches between patch blocks specified in expconf
  def loadPatchBlock(self,blockNumber):
    if (blockNumber>0):
      patchName = 'patch' + str(blockNumber)
    else:
      patchName = 'DEFAULT'
    
    # switching between versions
    if (expconf.cf.get(patchName,'delta_distr') == 'beta'):
      self.delta_a = expconf.cf.getfloat(patchName,'delta_a')  # beta distribution first param 
      self.delta_b = expconf.cf.getfloat(patchName,'delta_b')  # beta distribution second param
      self.delta_distr='beta'
    else:
      self.delta_m = expconf.cf.getfloat(patchName,'delta_m')  # exponential depletion rate
      self.delta_sd= expconf.cf.getfloat(patchName,'delta_sd')  # exponential depletion rate
      self.delta_distr='normal'
        
    self.Rmax   = expconf.cf.getfloat(patchName,'Rmax')  # exponential depletion rate
    self.blockname   = expconf.cf.get(patchName,'blockname')  # exponential depletion rate
    self.R0_m  = expconf.cf.getfloat(patchName,'R0_m')     # initial reward in a patch
    self.R0_sd = expconf.cf.getfloat(patchName,'R0_sd')     # initial reward in a patch
    self.t     = expconf.cf.getfloat(patchName,'t')        # delay to reward within a patch
    self.d     = expconf.cf.getfloat(patchName,'d')        # delay to a new patch
    self.cutoff= expconf.cf.getfloat(patchName,'cutoff') # cutoff where R becomes 0
    self.blockTime = expconf.cf.getfloat(patchName,'blockTime') # cutoff where R becomes 0
    self.patchIntroText = expconf.cf.get(patchName,'patchIntroText').replace("\\n","\n")
    self.breakText = expconf.cf.get(patchName,'breakText').replace("\\n","\n")
    self.delta = 1
    self.pR_rate  = expconf.cf.getfloat(patchName,'pR_rate')
    self.pR_m     = expconf.cf.getfloat(patchName,'pR_m')
    self.pR_sd    = expconf.cf.getfloat(patchName,'pR_sd')
    self.pRewardMode  = expconf.cf.getint(patchName, 'poissonRewardMode')
    self.showBreak=0

    # setting the background
    self.bgColorType   = expconf.cf.getint(patchName,'bgColorType') 
    bgcol              = expconf.cf.get('game','color_type' + str(self.bgColorType))
    self.backgroundCol = parseColor(bgcol)

    self.resetPReward()

    # loggin patch info
    if (blockNumber>0):
      logging.info(' -----------------------------------------')
      logging.info(' NEW PATCH INFO ')
      logging.info("Total handling time: " + str( expconf.cf.getfloat('game','delayToDecision') + 
                                     expconf.cf.getfloat('game','delayTooSlow') + 
                                     expconf.cf.getfloat('game','appleTime') + 
                                     expconf.cf.getfloat(patchName,'t') ) )

      logging.info("Total traveling time: " + str( expconf.cf.getfloat('game','delayToDecision') + 
                                     expconf.cf.getfloat('game','delayTooSlow') + 
                                     expconf.cf.getfloat(patchName,'d') ) )
                                     
      logging.info("Background color type: " + str(self.bgColorType))
      logging.info("Background color     : " + bgcol)
      logging.info("Irrelevant reward    : " + str(self.pR_rate))
      logging.info(' -----------------------------------------')

  # METHOD: reset patch when switch to a new tree
  def reset(self):
    self.delay   = self.t

    # here we are going to randomly draw the starting reward
    # in the current version of the model, we draw from a normal distribution 
    self.ireward = random.gauss(self.R0_m,self.R0_sd)  
    logging.info('starting at R0=' + str(self.ireward))

    logging.info('resetting the patch')
    self.state   = 1 
    self.computeReward() # adds the scaled noise on the reward

  # METHOD: update state to the next reward in the patch
  def next(self):    
    self.delay   = self.delay                  # delay within a patch doesn't change
    self.state   = self.state +1               # update the state everytime continue harvesting  

    # randomly draw the depletion rate from a beta distribution
    if (self.delta_distr=='beta'):
      self.delta = random.betavariate(self.delta_a, self.delta_b)
      self.ireward = self.ireward * self.delta
    else:
      # random draw for depletion from a normal- it has to be less than one so take 
      # min(draw,1) 
      for i in range(1,100):
        self.delta = random.gauss(self.delta_m , self.delta_sd) 
        # checking that the depletion rate is between 0 and 1
        # if (self.delta<0 ) | (self.delta>1):
        #  continue  # removed that because not in original experiment
        self.ireward = self.ireward * self.delta   # deplete previous R by delta
        if (self.ireward> 0) & (self.ireward<self.Rmax):
          break
        
    # just in case don't find a reward, bound it
    self.ireward = min(max( self.ireward, 0), self.Rmax)

    logging.info('continuing in patch, depleting reward')
    self.computeReward() # adds the scaled noise on the reward
 
  # METHOD: adds the multiplicative noise, which scales the variance to the current reward
  def computeReward(self):
    self.reward = self.ireward
    if (self.reward < self.cutoff):
      self.reward = 0
    logging.info('reward set to ' + str(self.reward) + ' / ' + str(self.ireward))

    if (self.reward - math.floor(self.reward)<0.05):
      self.reward = math.floor(self.reward)
    elif (self.reward - math.floor(self.reward)<0.1):
      self.reward = math.floor(self.reward) + 0.1

  # METHOD: get the current delay/reward 
  def getDelayReward(self):
    return self.delay, self.reward
   
  # Methods for irrelevant / poisson reward
  # =======================================

  def getPReward(self):
    """returns the value of the current poisson reward"""
    return self.preward
  
  # generate 
  def resetPReward(self):
    self.preward = random.gauss(self.pR_m , self.pR_sd)
    self.ptime   = np.random.exponential(self.pR_rate)

def parseColor(s):
  v = s.rsplit(',')
  return((int(v[0]),int(v[1]),int(v[2])))

