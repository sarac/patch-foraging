import os			      # command to deal with files / folders 
import pygame                 	      # main pygame library
from pygame.locals import *           # subfunctions in pygame
import logging	                      # logging to file 
from dataframe import DataFrame       # class to store data
import argparse			      # class to parse arguments
import time,sys,datetime,math,random  # 
import numpy as np                    # commment this if not working

from patchgenerator import PatchGenerator,parseColor
import expconf
from treesprites import *

class Trial(pygame.sprite.OrderedUpdates):
	# This class extends the class sprites to deal 
	# with the states of the game. Because trial is of the type
	# ordered updates and this class from which we inherit understands
	# that when we add each sprite it should be added to the screen
  
  # defining the states of the game
  STATE_WAITING_FOR_EXIT_DECISION   = 0  # subject has been prompted for a C/E decision but has not yet answered
  STATE_WAITING_FOR_NEXT_TREE       = 1  # subject has selected E and is waiting the delay to the new patch
  STATE_WAITING_FOR_REWARD          = 2  # subject has selected C and is waiting the delay t to the reward
  STATE_WAITING_FOR_REWARD_DELIVERY = 3  # subject has selected C and waited t and the apples are being shown
  STATE_TOO_SLOW_WARNING            = 4  # subject was prompted for a C/E decision but took too long to respond
  STATE_CHANGING_PATCH_BLOCK        = 5  # the block time is up and we switch to a new block with new parameters
  STATE_SHOW_BREAK                  = 6  # showing a break (inbetween blocks)
  STATE_TRANSFER_TO_DECISION        = 7  # small delay before next decision
  STATE_END_OF_GAME                 = 8  # game is over, screen shows this
  STATE_INSTRUCTIONS                = 9  # isnstructions shown at the beginning of the game
  STATE_IRRELEVANT_REWARD           = 10 # showing message for irrelevant reward

  def __init__(self,user,screen,background,recover=0,skipInstr=0): # need to initialize user outside (visible in main loop) and inside   
    pygame.sprite.OrderedUpdates.__init__(self)
    self.generator          = PatchGenerator() # create the patch
    self.user               = user
    self.background         = background
    self.tree_is_reset      = 0
    self.patchBlock         = 0
    self.delayTooSlow       = expconf.cf.getfloat('game','delayTooSlow') 
    self.numberOfPatchBlock = expconf.cf.getint('game','numberOfPatchBlock')
    self.delayToDecision    = expconf.cf.getfloat('game','delayToDecision')
    self.blockBreakLength   = expconf.cf.getfloat('game','blockBreakLength')
    self.applePrice         = expconf.cf.getfloat('game','applePrice')
    self.numApplePerRow     = expconf.cf.getint('game','numApplePerRow')
    self.showScorePerTrial  = expconf.cf.getint('game', 'showScorePerTrial')
    self.pDelay             = expconf.cf.getint('game', 'showPoissonRewardDelay')
    self.shakeTree          = expconf.cf.getint('game', 'shakeTree')
    #self.lengthTooSlow     = expconf.cf.getfloat('game','lengthTooSlow')
    self.color_instruction  = parseColor(expconf.cf.get('game', 'color_instruction'))
    self.ticker_speed       =  expconf.cf.getfloat('game', 'ticker.speed')
    self.ticker_speed2      =  expconf.cf.getfloat('game', 'ticker.speed2')
    self.ticker_show        =  expconf.cf.getfloat('game', 'ticker.show')
    self.forceStayFirstHarvest = expconf.cf.getint('game', 'forceStayFirstHarvest')
    self.randomApplePosition = expconf.cf.getint('game', 'randomApplePosition')
    self.extension = expconf.cf.get('main', 'save_extension')

    self.rt = -1
    self.decision =  UserAction.STATE_NONE
    self.totalCents = 0
    self.apples = list()
    self.scorePerTree = 0

    self.nTooSlowWarning = 0 # number of too slow warning on this action
    self.justEnteringTheStatePR=1

    # setting the logger
    self.logger = logging.getLogger('trial')                     # logging is a python class, this line adds trial infront of log                  
    self.deliveryDelay = expconf.cf.getfloat('game','appleTime')    # time for which we show the apples on the screen

    # get the first delay/reward
    self.delay , self.reward = self.generator.getDelayReward() 

    # creating the data set
    self.prepareData(recover)
    self.gstate =0

    # preparing starting of the experiment
    self.getPatchBlock(0)
    self.setState(Trial.STATE_INSTRUCTIONS)
    self.instrNumber = 1
    
    # if we recover, we skip instructions
    if (recover>0):
      self.setState(Trial.STATE_TRANSFER_TO_DECISION)
    elif (skipInstr):
      self.getNextPatchBlock()
      self.setState(Trial.STATE_TRANSFER_TO_DECISION)

    self.logger.info('decision time is %f' % self.delayTooSlow)
    
    # adding the sprites to the group
    r           = screen.get_rect().copy()      # gets size of rectangle of screen and creates a copy
    r           = r.move(0,int(-r.h/4))         # move rectangle shifted up by a 6th of its height
    self.center = r
    self.tree   = Tree(self.center.midbottom)   # center at the bottom of the rectangle
    self.add(self.tree)                         # append tree to list of sprites
    self.screen = screen
    #self.score  = Score(self.center.move(self.center.centerx/2 + 50,0).center)    # create the score sprite
    self.score  = Score(self.center.move(self.center.centerx/4 + 50,25).midbottom)    # create the score sprite
    self.poissonReward  = PoissonReward(self.center.center)    # create the score sprite
    
    # add fixation
    r2 = r.copy()
    r2.midbottom = screen.get_rect().midbottom 
    #self.fixationCross = FixationCross(r.move(0,-280).midbottom) # move down from bottom of tree
    self.fixationCross = FixationCross(r.move(0,25).midbottom,expconf.cf.get('game', 'fixationShape')) # move down from bottom of tree
    self.add(self.fixationCross)
    self.fixationCross.activate()                                # start at the decision

    # adding warning sprites
    self.warning = ImageBox('tooSlowWarning.png',self.center.center)

    # adding sounds
    self.reward_sound = load_sound('img/coinsdrop_short.wav')

    # adding ticker
    self.ticker = Ticker(self.center.center,self.ticker_speed2)
    self.ticker.setAngle(45)
   

    # debugging the textbox
    self.textbox = TextBox(screen.get_rect().center)

    # 
    self.totalInstrNumber = expconf.cf.getint('INSTRUCTIONS','totalInstrNumber')
    self.instrMinLength   = expconf.cf.getint('INSTRUCTIONS','instrMinLength')

  # prepare data saving mechanism
  # if we are in recover mode, read the file from the drive
  def prepareData(self,recover):
    self.data  = DataFrame(expconf.cf.get('subject','datafile') + '_data.csv')    # for decisions
    self.adata = DataFrame(expconf.cf.get('subject','datafile') + '_action.csv')  # for state changes

    # RECOVERING
    # =========
    if (recover==1):
      # load data from file
      self.data.load()
      self.adata.load()

      cr = self.data.getCurrentRow()

      # set Trial to use correct patch block - and time
      self.patchBlock = int(cr['patchBlock'])
      self.patchBlockType = expconf.gameseq[self.patchBlock]
      self.getPatchBlock(self.patchBlockType)
      self.lastBlockUpdate =  pygame.time.get_ticks() - int(1000*float(cr['blockTime']))

      # set patch generator to correct patch state and internal reward
      self.generator.state   = int(cr['patchState'])
      self.generator.ireward = float(cr['patchInternalReward'])
      self.totalCents        = float(cr['totalCents'])

      self.logger.info('Recovered session, starting at (b=%i,s=%i,bt=%i,pd=%i,pt=%i)',self.patchBlock,
                           self.generator.state,int(self.blockTime()),
                           int(self.generator.ptime),int(self.pTime()))

  def resetTime(self):
    self.lastUpdate = pygame.time.get_ticks()
    
  def resetPTime(self):
    self.lastPTime = float(pygame.time.get_ticks())/1000

  def pTime(self):
    return float(pygame.time.get_ticks())/1000 - self.lastPTime

  def resetBlockTime(self):
    self.lastBlockUpdate = pygame.time.get_ticks()
    self.resetPTime()
    
  # return the current elapsed time
  def time(self):
    return float(pygame.time.get_ticks() - self.lastUpdate)/1000

  def blockTime(self):
    return float(pygame.time.get_ticks() - self.lastBlockUpdate)/1000

  # set the state to the current state and reset the time
  def setState(self,state):
    # logging
    self.logger.info('State changes from %i to %i (b=%i,s=%i,bt=%i,pd=%i,pt=%i)',self.gstate,state,self.patchBlock,
                                self.generator.state,int(self.blockTime()),int(self.generator.ptime),int(self.pTime())) 

    self.gstate = state
    self.resetTime()
    self.justEnteringTheState = 1
    self.saveStateChange(state)

  def getPatchBlock(self,b):
    self.generator.loadPatchBlock(b)
    self.background.fill(self.generator.backgroundCol)
    self.resetBlockTime()

  def getNextPatchBlock(self):
    # get the next patch block from the game sequence 
    self.patchBlock = self.patchBlock + 1
    self.patchBlockType = expconf.gameseq[self.patchBlock-1]
    self.getPatchBlock(self.patchBlockType)
    self.generator.showBreak=( self.patchBlock in expconf.breakseq)

  # IMPORTANT STATE LOGIC FOR TRIAL
  # ==============================
  def update(self):      

    # updating the ticker
    if (self.ticker_show):
      self.add(self.ticker)
      self.ticker.setAngle(self.ticker_speed /self.generator.pR_rate * self.blockTime())
      self.ticker.setCount(self.generator.pR_m /self.generator.pR_rate * self.blockTime(),self.generator.backgroundCol)

    ######### CHECKING IF WE NEED TO CHANGE PATCH BLOCK : Happens in all states ##########
    if ((self.blockTime() > self.generator.blockTime) & 
        (self.patchBlock>0) & 
        (self.gstate != Trial.STATE_SHOW_BREAK) &
        (self.gstate != Trial.STATE_CHANGING_PATCH_BLOCK)):
      if (self.patchBlock == self.numberOfPatchBlock):
        if (self.gstate!=Trial.STATE_END_OF_GAME):
          self.setState(Trial.STATE_END_OF_GAME)
      else:
        self.logger.info("changing patch block")
        self.empty()
        if self.generator.showBreak==1:
          self.setState(Trial.STATE_SHOW_BREAK)
        else: 
          self.setState(Trial.STATE_CHANGING_PATCH_BLOCK)
        self.resetBlockTime()
        self.getNextPatchBlock()
        return
              
    ######### STATE: INSTRUCTIONS ##########
    if self.gstate == Trial.STATE_INSTRUCTIONS:
      if (self.justEnteringTheState):
        self.tree.pos=(self.tree.diameter,self.tree.pos[1])  #puts tree to the left
        self.justEnteringTheState = 0
        self.user.foreaging == UserAction.STATE_NONE
        self.empty()
        self.background.fill(self.color_instruction)
        
        # depending on the current instruction slide we are going to display different things
        if (self.instrNumber == 2):
          # if you want to add a tree for instruction
          self.add(self.tree)
          self.addApples(6.5,-525)
          
        # depending on the current instruction slide we are going to display different things
        if (self.extension=='train'):
            if (self.instrNumber == 3):
              # if you want to add a tree for instruction
              self.add(self.tree)
              # note: position needs to be to right of text and should have white cross on it
              self.fixationCross.pos = (self.tree.pos[0],self.fixationCross.pos[1])
              #self.fixationCross.activate()
              self.fixationCross.deactivate()
              self.add(self.fixationCross)
 
            elif (self.instrNumber == 4):
            # we add some apples
              self.addApples(10,-400,-60)
              self.addApples(6.2,0,-60)
              self.addApples(3.5,400,-60)
          
            if (self.instrNumber == 5):
              # if you want to add a tree for instruction
              self.add(self.tree)
              # note: position needs to be to right of text and should have white cross on it
              self.fixationCross.pos = (self.tree.pos[0],self.fixationCross.pos[1])
              self.fixationCross.deactivate()
              self.add(self.fixationCross)
           
            if (self.instrNumber == 6):
              # if you want to add a tree for instruction
              self.add(self.tree)
              # note: position needs to be to right of text and should have white cross on it
              self.fixationCross.pos = (self.tree.pos[0],self.fixationCross.pos[1])
              self.fixationCross.activate()
              self.add(self.fixationCross)
          
            if (self.instrNumber == 7):
              # if you want to add a tree for instruction
              self.add(self.tree)
              # note: position needs to be to right of text and should have white cross on it
              self.fixationCross.pos = (self.tree.pos[0],self.fixationCross.pos[1])
              self.fixationCross.deactivate()
              self.add(self.fixationCross)          
           
            elif (self.instrNumber == 8):
              self.tree.pos=self.center.midbottom # to recenter the tree
              self.add(self.tree)
              self.fixationCross.pos = (self.tree.pos[0],self.fixationCross.pos[1])
              self.fixationCross.deactivate()
              self.add(self.fixationCross)
              self.add(self.warning)
          
            elif (self.instrNumber == 11):
              self.background.fill(self.generator.backgroundCol)
              # we need a new text box
              textbox2 = TextBox(self.screen.get_rect().center)
              textbox2.col = (250,0,0)
              textbox2.setText(self.generator.patchIntroText,self.generator.backgroundCol)
              self.add(textbox2)
          
            if (self.instrNumber == 12):
              # if you want to add a tree for instruction
              self.add(self.tree)
              # note: position needs to be to right of text and should have white cross on it
              self.addApples(8.5,-525)
          
            #if (self.instrNumber == 14):
              ## if you want to add a tree for instruction
              #self.add(self.tree)
              ## note: position needs to be to right of text and should have white cross on it
              #self.addApples(13.5,-525)          
                    
        #self.empty()
        # getting the instruction text
        instrText = expconf.cf.get('INSTRUCTIONS','instrText' + str(self.instrNumber)).replace("\\n","\n")
        self.textbox.setText(instrText,self.color_instruction)
        self.add(self.textbox)
          
      # ---- dealing with the exiting of the state
      # state dependend exit
      doexit =  (self.user.foreaging == UserAction.STATE_SPACEBAR) | (self.user.foreaging == UserAction.STATE_LEFT)
   
      # use doexit with minimum delay
      if (doexit &  (self.time() > self.instrMinLength)):
        self.removeApples()
        self.empty()
        
        # if we are at the last instruction, we can move to the first block
        if (self.instrNumber == self.totalInstrNumber):
          self.background.fill(self.generator.backgroundCol)
          self.setState(Trial.STATE_CHANGING_PATCH_BLOCK)
          self.getNextPatchBlock() # going to first patch 
        #otherwise, we go to the next instruction
        else:
          if ((self.user.foreaging == UserAction.STATE_SPACEBAR)):
            self.instrNumber = self.instrNumber + 1
          else:
            self.instrNumber = self.instrNumber - 1              
          self.setState(Trial.STATE_INSTRUCTIONS) 
   
    ######### STATE END OF GAME ###########
    elif self.gstate == Trial.STATE_END_OF_GAME:
      if (self.justEnteringTheState):
        self.empty()
        self.justEnteringTheState = 0       

        self.textbox.setText('Game over!\n You will receive an extra: \n' + '$' + str(int((int(self.totalCents*100)/100.0))/100.0),self.generator.backgroundCol)
        self.add(self.textbox) 
    
    ######### WAITING FOR REWARD ##########
    elif self.gstate == Trial.STATE_WAITING_FOR_REWARD:
      if (self.justEnteringTheState):
        if (self.shakeTree):
          self.tree.isShaking = 1 # comment this to remove shaking
        self.justEnteringTheState = 0

      # ------- change state to reward state and add apples if delay is passed -------
      if ((self.time() > self.delay)): 
        self.tree.isShaking=0
        self.setState(Trial.STATE_WAITING_FOR_REWARD_DELIVERY)  
        self.logger.info('changing trial state to waiting for reward to be delivered')

    ######### STATE WAITING FOR REWARD DELIVERY ##########
    elif self.gstate == Trial.STATE_WAITING_FOR_REWARD_DELIVERY:
      if (self.justEnteringTheState):
        self.remove(self.fixationCross)
        self.addApples()
        self.justEnteringTheState=0

      # ------- change state if reward display delay has passed to waiting for a decision -------
      if ((self.time() > self.deliveryDelay)):  
        self.setState(Trial.STATE_TRANSFER_TO_DECISION)  
        self.logger.info('changing trial state to waiting for exit decision')
        self.removeApples()
        self.add(self.fixationCross)
        
        # get the next delay/reward
        self.generator.next()
        self.delay , self.reward = self.generator.getDelayReward()

    ######### STATE WAITING FOR EXIT DECISION ##########
    elif self.gstate == Trial.STATE_WAITING_FOR_EXIT_DECISION:
      if (self.justEnteringTheState):
        self.user.foreaging = UserAction.STATE_NONE # getting rid any previous action
        self.fixationCross.activate()
        self.justEnteringTheState=0
        self.decision =  UserAction.STATE_NONE

      # -------- store the first decision --------
      if  ((self.decision == UserAction.STATE_NONE)  & 
          (self.user.foreaging == UserAction.STATE_EXIT) &
          (self.generator.state==1) & 
          (self.forceStayFirstHarvest)):
          self.decision == UserAction.STATE_NONE
      elif ((self.decision == UserAction.STATE_NONE) & ( 
                (self.user.foreaging == UserAction.STATE_EXIT) | 
                (self.user.foreaging == UserAction.STATE_STAY))):
        self.decision = self.user.foreaging
        self.rt = self.time()                      # store the reaction time
        self.fixationCross.deactivate()
        if ((self.user.foreaging == UserAction.STATE_STAY) & self.shakeTree):
          self.tree.isShaking = 1 # comment this to remove shaking
        if ((self.user.foreaging == UserAction.STATE_EXIT) & self.shakeTree):
          self.tree.setAlpha(120) # comment this to remove shaking
             
      # ------- after delay, change to a new patch if get a choice of E -------
      if ((self.time() > self.delayTooSlow) & (self.decision==UserAction.STATE_EXIT)): 
        # save the data
        self.saveAction("exit")

        # create the new patch and get the next delay/reward
        self.generator.reset()
        self.delay , self.reward = self.generator.getDelayReward()
       
        # change the state
        self.setState(Trial.STATE_WAITING_FOR_NEXT_TREE)
        self.logger.info('changing trial state to waiting for next tree')
        self.fixationCross.deactivate()

      # ------- after delay, change states within a patch if get a choice of C -------
      elif ((self.time() > self.delayTooSlow) & (self.decision==UserAction.STATE_STAY)):
        # save the data
        self.saveAction("stay")

        # update the state
        self.setState(Trial.STATE_WAITING_FOR_REWARD)
        self.logger.info('changing trial state to waiting for next reward')
        self.fixationCross.deactivate()
      
      # ------- if too slow, show warning -------
      elif (self.time() > self.delayTooSlow):
        self.setState(Trial.STATE_TOO_SLOW_WARNING)
        self.fixationCross.deactivate()
        return

    ######### STATE_TRANSFER_TO_DECISION  -----  show black for few seconds #########
    elif self.gstate == Trial.STATE_TRANSFER_TO_DECISION:
      if (self.time() > self.delayToDecision):
        self.setState(Trial.STATE_WAITING_FOR_EXIT_DECISION)
        return

    ######### STATE WAITING FOR NEXT TREE -- CHANGING THE TREE #########
    elif self.gstate == Trial.STATE_WAITING_FOR_NEXT_TREE: 
      if (self.justEnteringTheState):
        self.justEnteringTheState=0
        self.tree_is_reset = 0

      # positioning the tree
      # we look at how much time is left to find how far we 
      # should be from the end point
      ratioTime = min(1 , 1.1 * self.time()/self.generator.d) # time since entered state/d, tells you percentage movement
      # if time < 0.5 total time
      #position = ratioTime * rate
      # if stroop = 1
      #new time = total time + stroop time
      #ratio Time = reflects new time
      #position = new ratio Time * rate 
      # then we compute where the tree should be
      self.tree.setPosition(ratioTime,self.screen.get_rect().w)   
      #will be setPosition(ratioTime,
      if ((self.tree_is_reset==0) & (ratioTime>=0.5)):
        self.tree.reset()
        self.tree_is_reset = 1

      if ((self.time() > self.generator.d)):
        #self.remove(self.score)
        self.scorePerTree = 0                                  
        self.setState(Trial.STATE_TRANSFER_TO_DECISION)  
        self.logger.info('changing trial state to waiting for exit decision')

    ######### STATE TOO SLOW WARNING -- SHOWING WARNING #########
    # this state represents a one trial cycle delay because it is
    # 1 sec to make the decision, which they missed
    # t to reward
    # 1 sec of apple display (deliveryDelay)
    # 0.5 sec additional to next decision
    elif self.gstate == Trial.STATE_TOO_SLOW_WARNING: 
      if (self.justEnteringTheState):
        self.add(self.warning)
        self.justEnteringTheState=0
        self.nTooSlowWarning = self.nTooSlowWarning +1
      # we show the warning, and we move back to exit decision

      if (self.time() > self.generator.t + self.deliveryDelay):
        self.remove(self.warning )
        self.setState(Trial.STATE_TRANSFER_TO_DECISION)  
        self.logger.info('changing trial state to waiting for exit decision')
    
    ######### STATE_CHANGING_PATCH_BLOCK #############
    elif self.gstate == Trial.STATE_CHANGING_PATCH_BLOCK:
      self.resetBlockTime() # reset block time to 0 -- to avoid switching to block 3 while on break between 1 and 2

      # we need to reset the tree, since it might be in 
      # any position
      if (self.justEnteringTheState):
          self.justEnteringTheState = 0
          self.scorePerTree = 0
          self.tree.reset()
          self.tree.isShaking = 0
          self.tree.setPosition(0,self.screen.get_rect().w)
          self.empty()  
          if (self.patchBlock>1):
              self.textbox.setText(self.generator.patchIntroText,self.generator.backgroundCol)
              self.add(self.textbox)
          
      # waiting for delay + space bar key press
      if ( (self.patchBlock==1) | (( self.user.foreaging == UserAction.STATE_SPACEBAR) & (self.time() > self.blockBreakLength))):
        self.add(self.tree)
        self.add(self.fixationCross)
        self.remove(self.textbox)
        self.resetBlockTime() # reset block time to 0
        self.setState(Trial.STATE_TRANSFER_TO_DECISION)
      elif (self.time() > self.blockBreakLength):
        self.user.foreaging == UserAction.STATE_NONE
        
    ######### STATE_SHOW_BREAK #############
    elif self.gstate == Trial.STATE_SHOW_BREAK:
      if (self.justEnteringTheState):
        self.justEnteringTheState = 0
        self.empty()  
        self.textbox.setText(self.generator.breakText,self.color_instruction)
        self.add(self.textbox)
        self.background.fill(self.color_instruction)
          
      # waiting for delay + sapce bar key press
      if (( self.user.foreaging == UserAction.STATE_SPACEBAR) & (self.time() > self.blockBreakLength)):
        self.remove(self.textbox)
        self.background.fill(self.generator.backgroundCol)
        self.setState(Trial.STATE_CHANGING_PATCH_BLOCK)
      elif (self.time() > self.blockBreakLength):
        self.user.foreaging == UserAction.STATE_NONE
        
    else:
      pass
    
    ######### SHOWING THE IRRELEVANT REWARD ########
    if ( ( (self.gstate != Trial.STATE_END_OF_GAME)  | (self.justEnteringTheStatePR==0)) &
         ( (self.gstate != Trial.STATE_SHOW_BREAK)   | (self.justEnteringTheStatePR==0)) &
         ( (self.gstate != Trial.STATE_INSTRUCTIONS) | (self.justEnteringTheStatePR==0)) & 
         (self.generator.pRewardMode>0) & (self.pDelay>0) & (self.pTime() > self.generator.ptime)):
      if (self.justEnteringTheStatePR):
        self.saveAction("poissonreward")
        self.totalCents = self.totalCents + self.generator.preward  # adding reward to total money

        if (self.generator.pRewardMode in (1,3)):
          self.add(self.poissonReward)
          self.poissonReward.setPReward(self.generator.preward)
        if (self.generator.pRewardMode in (2,3)) :
          self.reward_sound.play()
        self.justEnteringTheStatePR=0
      
      if (self.pTime() > self.generator.ptime + self.pDelay):
        self.logger.info('done delivering the irrelevant reward')
        if (self.generator.pRewardMode in (1,3)):
          self.remove(self.poissonReward)
        self.generator.resetPReward()
        self.resetPTime()
        self.justEnteringTheStatePR=1

    ### call the update method on the 
    # mother class
    pygame.sprite.Group.update(self)     # call update on the class Group we are extending from module sprite

  def saveAction(self,decision):
    self.data.newRow()
    if (self.rt>self.delayTooSlow):
      self.logger.info(">>>>>> rt larger than max delay (%f > %f" % (self.rt,self.delayTooSlow))
    self.data["rt"]                  = self.rt
    self.data["time"]                = pygame.time.get_ticks()
    self.data["abstime"]             = time.time()
    self.data["decision"]            = decision
    self.data["delaySamePatch"]      = self.delay
    self.data["depletionRate"]       = self.generator.delta

    if (self.generator.delta_distr=='beta'):
      self.data["depletionRate_alpha"] = self.generator.delta_a    
      self.data["depletionRate_beta"]  = self.generator.delta_b    
      self.data["depletionRate_distr"]  = 'beta' 
    else:
      self.data["depletionRate_m"] = self.generator.delta_m
      self.data["depletionRate_sd"]  = self.generator.delta_sd
      self.data["depletionRate_distr"]  = 'normal' 
    self.data["R0_m"]                = self.generator.R0_m    
    self.data["R0_sd"]               = self.generator.R0_sd    
    self.data["bgcolor"]             = hex(self.generator.backgroundCol[2] + self.generator.backgroundCol[1]*256 + self.generator.backgroundCol[0]*(256**2))
    self.data["poissonReward"]       = 0
    if decision == 'exit':
      self.data["reward"]              = 0
      self.data["patchInternalReward"] = 0 
    elif decision == 'poissonreward':
      self.data["poissonReward"]       = self.generator.preward
      self.data["reward"]              = 0
      self.data["patchInternalReward"] = 0 
    else:
      self.data["reward"]              = self.reward
      self.data["patchInternalReward"] = self.generator.ireward
    self.data["delayOtherPatch"]     = self.generator.d
    self.data["patchState"]          = self.generator.state
    self.data["patchBlock"]          = self.patchBlock
    self.data["blockTime"]           = self.blockTime()
    self.data["nWarning"]            = self.nTooSlowWarning
    self.data["totalCents"]          = self.totalCents
    self.data["blockName"]           = self.generator.blockname    
    self.data["PR_rate"]             = self.generator.pR_rate  
    self.data["pR_m"]                = self.generator.pR_m  
    self.data["pR_sd"]               = self.generator.pR_sd  

    self.data.save()
    self.nTooSlowWarning = 0

  def saveStateChange(self,state):
    self.adata.newRow()
    self.adata["time"]                = pygame.time.get_ticks()
    self.adata["abstime"]             = time.time()
    self.adata["patchState"]         = self.generator.state
    self.adata["patchBlock"]         = self.patchBlock
    self.adata["state"]              = state
    self.adata.save()
 
  # function that generates the apples
  def addApples(self,areward=-1,hshift=0,vshift=0):

    if (areward==-1):
        areward = self.reward

    self.logger.info('Adding the apples (' + str(areward) + ')')
    self.apples = list()                                                # empty list of apples

    # generate full apples
    self.logger.info("adding the apples :" + str( math.floor(areward)  ))
    for i in range(1,int(math.floor(areward))+1):                                 # one apple for each integer reward
      # take x randomly
      if (self.randomApplePosition):
        x,y = self.findNewApplePosition()
      else:
        x,y = self.findNewApplePositionRow()
        x = x + hshift
        y = y + vshift
        
      apple = Apple(self.center.move(x,y).midbottom, 1,'img/' + expconf.cf.get('game','rewardImage'))                 
      # rand normal position, move rect then take midbottom
      self.add(apple)
      self.apples.append(apple)                                         # append object apple to the list of apples

    # generate the partial apple
    # get the remainder 
    rem =areward - math.floor(areward)
    if (rem>0):
      if (self.randomApplePosition):
        x,y = self.findNewApplePosition()
      else:
        x,y = self.findNewApplePositionRow()
        x = x + hshift
        y = y + vshift
      apple = Apple(self.center.move(x,y).midbottom , rem)
      self.add(apple)
      self.apples.append(apple)
      self.logger.info("adding a portion of an apple :" + str(rem) + ' ('+ str(areward)  +')')

    # add the score
    self.cents = int(areward*self.applePrice * 100)/100.0
    self.score.setScore(self.cents)
    if self.showScorePerTrial==1:
      self.add(self.score)
      
    self.totalCents = self.totalCents + self.cents
    self.logger.info("adding reward to total :" + str(self.cents) + ' ('+ str( self.totalCents)  +' / ' + str( areward) +')')
    self.scorePerTree = self.scorePerTree + self.cents
    
    return self.apples
  

  def findNewApplePosition(self):
    # looking for a random position for new apples
    for i in range(1,200):
      x = int(random.gauss(0,1)*80)
      y = int(random.gauss(0,1)*10)
      
      # check if it's close to any other apple
      keep = True
      for a in self.apples:
        if ((a.pos[0] - self.center.centerx - x)**2 + (a.pos[1]-self.center.bottom-y)**2)<(0.8*a.rect.w)**2:
          keep = False
          break

      if keep:
        return (x,y)

    self.logger.info("unable to find new position for the apples")
    return (x,y)

  def findNewApplePositionRow(self):
    # we want to put apples in row of 6
    # we need to compute the position of each of those apples
    n = len(self.apples) + 1
  
    # compute the position in the grid of apples
    r = math.floor( (n-0.001)/self.numApplePerRow )
    c = n - self.numApplePerRow*r -1
    
    a = Apple((0,0),1)
    x = c*( a.rect.w * 1.1 )
    y = r*( a.rect.h * 1.1 )
  
    # centering the apple
    x = x - (self.numApplePerRow/2) * 1.1 * a.rect.w

    return (x,y)

  def removeApples(self):
    self.logger.info('removing apples')
    for a in self.apples:                                                # remove all apples in the list
      self.remove(a)
    del self.apples
    self.apples = list()
    if self.showScorePerTrial==1:
      self.remove(self.score)

# -----------------------------------------
# Classes that handle experiment logic
# -----------------------------------------
class UserAction:
  # this class codes for the decision and
  # is updated in class trial and the 
  # experiment loop 
  STATE_NONE = 0
  STATE_EXIT = 1
  STATE_STAY = 2
  STATE_SPACEBAR = 3
  STATE_LEFT = 4

  def __init__(self):
    self.foreaging = UserAction.STATE_NONE

