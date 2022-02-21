#!/usr/bin/env python2.6
"""
               SIMPLE FORAGING TASK IN AN ENVIRONMENT WITH DEPLETING REWARDS
----------------------------------------------------------------------------------------------
This experiment is similar to the fishing version but with fewer visual stimuli
and less animation (in preparation for fmri). The experiment is a simple
patch-foraging study with an exponentially depleting patch. On each trial the
subject can decide to exit or to continue foraging.

Steps Of The Game:
  1) Start at a tree and make a C/E decision by pressing RIGHT or DOWN
  2) if DOWN - the tree is for
     a) the apples are depleting at rate alpha
     b) apples are worth X cents each, the total earned is flashed on the screen at the end of the experiment
  3) if RIGHT - the tree fades and transitions to a new, unharvested tree with some small animation
  4) Subject makes a C/E decision
  
Notes:
The subject cannot change his mind, once a decision is made the next state triggered. The wait time however is always fixed regardless of 
the key press to minimize differences in reward rate due to reaction time.

Required modules:
get numpy for osx    : http://stronginference.com/scipy-superpack/
get pygame from      : main site
get pydataframe from : http://pypi.python.org/pypi/pydataframe/0.1#downloads

HELP REMINDERS 
  
  to run an experiment in debug mode:
  python tree_game.py -d -i
  
  to get help do:
  python tree_game.py -h
"""  

# Import external libraries
# -------------------------
import os           # command to deal with files / folders 
import pygame                         # main pygame library
from pygame.locals import *           # subfunctions in pygame
import logging                        # logging to file 
from dataframe import DataFrame       # class to store data
import argparse                       # class to parse arguments
import time,sys,datetime,math,random  # 
import ConfigParser                   # parsing of ini files

# Import internal libraries 
# --------------------
import expconf
import exploop              # class that handles the sequencing of STATES in the experiment

# =================================================
#         THIS IS WHERE PYTHON STARTS
# =================================================

def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def parseGameSeq(s):
  v = s.rsplit(',')
  r = []
  rbreak = []
  bn = 0
  for val in v:
    if is_number(val):
      bn = bn +1
      r.append(int(val))
    elif val=='break':
      rbreak.append(bn)

  return r,rbreak

#calls the 'main' function when this script is executed
if __name__ == '__main__': 
  
  # Setting shell arguments
  # -------------------------
  parser = argparse.ArgumentParser(
      description ='Run the tree experiment and save the info to a file',
      epilog      ="Data is stored in CSV file, use column -s, -t tmp.csv to see it! \n Quick run, do python main.py -d -i")

  parser.add_argument('-l',action='store_true',help='logs to the console, instead of a file')
  parser.add_argument('-w',action='store_true',help='run the program within a window - not in full screen')
  parser.add_argument('-i',action='store_true',help='skip instructions')
  parser.add_argument('-c',action='store',nargs=1,help='specify version of ini file, for example use delay for expconf.delay.ini. Common options are in expconf.all.ini',metavar='configversion')
  parser.add_argument('-g',action='store',default=0,nargs=1,help='specify which game sequence to use')

  group_new = parser.add_argument_group('new', 'run a new experiment with new subject information')
  group_new.add_argument('-n', action='store', nargs=1,help='name or intials of the subject',metavar='name')
  #group_new.add_argument('-a', type=int, action='store',nargs=1,help='age of the subject',metavar='age')  
  #group_new.add_argument('-e', action='store', nargs=1,help='email of the subject',metavar='email')
  #group_new.add_argument('-s',action='store',choices=['male','female'], nargs=1,default="male",help='sex of the subjet')
  group_new.add_argument('-hand',action='store',choices=['left','right'], nargs=1,default="right",help='handness of the subjet')

  group_recover = parser.add_argument_group('recover', 'recover information and data from previous experiment')
  group_recover.add_argument('-r',action = 'store_true', help=' add this argument to recover' )

  group_debug = parser.add_argument_group('debug', 'runs without saving anything')
  group_debug.add_argument('-d',action = 'store_true')

  args = parser.parse_args()

  # Loading config file 
  # -------------------

  expconf.cf = ConfigParser.ConfigParser()  # creates object of type config.parser
  recover=0
  
  # form ini file name
  if (args.c):
    INI_FILE_NAME = 'expconf.' +  args.c[0] + '.ini'
  else:
    INI_FILE_NAME = 'expconf.default.ini'

  print "Using following expconf file: ", INI_FILE_NAME

  if (args.r):
    print "Recovering crashed experiment..."
    # loads the experiment parameters from last experiment
    expconf.cf.read('tmp.expconf.ini')      
    print "data file : ",expconf.cf.get('subject', 'datafile')
    
    # reloading the game sequence
    expconf.gameseq , expconf.breakseq = parseGameSeq(expconf.cf.get('game','gameSequence'))
    raw_input("Press any Key")
    recover=1

  # DEBUG MODE
  # ----------
  elif (args.d):
    # read default file
    expconf.cf.read(('expconf.all.ini',INI_FILE_NAME))          

    # add the subject details and date
    expconf.cf.add_section('subject')

    # create the name file for data storate
    filename =  expconf.cf.get('main','datafolder') + '/.tmp.exp' 
    expconf.cf.set('subject', 'datafile', filename)

    # randomizing colors -- there are 4 colors, randomize the block-color association
    colorArray = range(1, expconf.cf.getint('game','ncolors')+1) 
    random.shuffle(colorArray)
    for i in range(1, expconf.cf.getint('game','ncolors')+1) :
      expconf.cf.set('game','color_type' + str(i), expconf.cf.get('DEFAULT','color'+str(colorArray[i-1])))

    # randomizing game sequence
    if (args.g):
      gameseq = int(args.g[0])
    else:
      gameseq = random.randint(1, expconf.cf.getint('game','gameSequenceN'))

    expconf.cf.set('game','gameSequence', expconf.cf.get('game','gameSequence'+str(gameseq)))
    expconf.gameseq , expconf.breakseq = parseGameSeq(expconf.cf.get('game','gameSequence'+str(gameseq)))

    # save to tmp file for possible recovery
    with open('tmp.expconf.ini', 'wb') as f:
      expconf.cf.write(f)
   
  # NORMAL MODE
  # ----------- 
  else:
    # read default file
    expconf.cf.read(('expconf.all.ini',INI_FILE_NAME))          

    # add the subject details and date
    date = datetime.datetime.now().strftime("%d%B%Y") 
    expconf.cf.add_section('subject')
    expconf.cf.set('subject', 'name', args.n[0])
    expconf.cf.set('subject', 'hand', args.hand)
    #expconf.cf.set('subject', 'age',  args.a[0])
    #expconf.cf.set('subject', 'email',args.e[0])
    #expconf.cf.set('subject', 'sex'  ,args.s[0])
    expconf.cf.set('subject', 'date', date)
    save_extension = expconf.cf.get('main','save_extension')

    # create the name file for data storate
    filename =  expconf.cf.get('main','datafolder') + '/expconf_' +  expconf.cf.get('main','version') + '_' +  args.n[0] + '_' + date + '_' + save_extension
    expconf.cf.set('subject', 'datafile', filename)

    # randomizing colors -- there are 4 colors, randomize the block-color association
    colorArray = range(1, expconf.cf.getint('game','ncolors')+1) 
    random.shuffle(colorArray)
    for i in range(1, expconf.cf.getint('game','ncolors')+1) :
      expconf.cf.set('game','color_type' + str(i), expconf.cf.get('DEFAULT','color'+str(colorArray[i-1])))

    # randomizing game sequence
    if (args.g):
      gameseq = int(args.g[0])
    else:
      gameseq = random.randint(1, expconf.cf.getint('game','gameSequenceN'))
    expconf.cf.set('game','gameSequence', expconf.cf.get('game','gameSequence'+str(gameseq)))
    expconf.gameseq , expconf.breakseq = parseGameSeq(expconf.cf.get('game','gameSequence'+str(gameseq)))

    # save to tmp file for possible recovery
    with open('tmp.expconf.ini', 'wb') as f:
      expconf.cf.write(f)
    with open(expconf.cf.get('subject','datafile') + '_conf.ini', 'wb') as f:
      expconf.cf.write(f)

  if (args.l):
    logging.basicConfig(level=logging.INFO)  # can choose which logging level is displayed, here choose INFO
  else:
    logging.basicConfig(filename= expconf.cf.get('subject','datafile') + '_all.log',level=logging.INFO)
    print 'logging to ',expconf.cf.get('subject','datafile') + '_all.log'

  # adding the screen config
  expconf.cf.set('main','fullscreen',str(1-int(args.w)))
  logging.info('using game sequence: ' + expconf.cf.get('game','gameSequence'))

  print " ==========  Starting Experiment ========="

  # calling start of the experiment
  # calling function form TreeExpMainLoop

  exploop.startExp(recover,args.i) 

