# TreeExp - for users

## experiment configuration

The first thing to do is to write a configuration file, an `expconf` file. This
contains the different parameters required for the experiment to be ran.

The file allows the user to define patches, each with their own parameters.
Then sequences of blocks and randomization over them can also be defined.

Let's take `expconf.default.ini` as an example, it defines 4 patches (1,2,3,4). For example here is patch 1:

    patchIntroText = Okay, you are now ready to begin the game! \n \n [Press Spacebar to continue]
    d              = 10.5       ; delay to a new patch such that optimal exit rule is 4 (d = d + 1.5 = 4.5)                                                                                                                                                                    
    delta_m        = 0.9433
    delta_sd       = 0.06
    bgColorType    = 1       ; background color of block
    blockname      = long-shallow

In addition to those, the file defines gamesequences that describes how the patches should be sequenced:

    numberOfPatchBlock         = 4         ; total number of patch blocks (count even if the same parameters)
    gameSequenceN              = 2 
    gameSequence1              = 1,2,break,1,2,end ;
    gameSequence2              = 2,1,break,2,1,end ;

Which says that they are 2 different types of game sequences, depending on the first block. Each game sequence has a break in the middle.
The experiment code will automatically randomize over the 2 sequences. Note that here we are not even using all the blocks, just 1 and 2.

Save your config file to `expconf.myconf.ini` in the same folder as the experiment code.

## experiment configuration

Once your expconfig file is ready, running the code is quite straightforward. You only need to call the program with the correct parameters.
So if you want to just test your config file, you do should run the following:

    python main.py -d -w -l -c myconf

The `-d` runs the debug code which means that nothing is saved, `-w` is to run within a window instead of fullscreen and `-l`
is to log everything directly to the console.

When you want to run a subject with name toto and age 34 you can do the following:

    python main.py -n toto -a 34 -c myconf

then the experiement data will be saved to the the disk.


# TreeExp - for developers

The code is written in [python](http://python.org) and uses [pygames](http://www.pygame.org/news.html) for rendering. Before going through this code try to get confortable with both.

 - [short intro to classes in python](http://www.jesshamrick.com/2011/05/18/an-introduction-to-classes-and-inheritance-in-python/)

## overview of the files

### main.py 

This is the entry point, it's where the program start. It parses the input arguments, loads the config files and initializes the graphic window. The last command calls `exploop.startExp` which is defined in the next file.

### exploop.py

This file runs the main loop required for pygame to work. An infinite loop runs at a very high frequency (every 30ms) to capture all keyboard inputs and perform all required updates of the screen such as showing trees, apples, instructions and removing then. 

The loop in exploop.py doesn't do that directly, it delegates most of the work by calling `trial.update()` at each cycle. The `update` method is defined in the next file.


### statelogic.py and the class Trial

The `Trial` class is possibly the most important part of the code. It defines the sequencing of events of the experiment. As mentioned before every about 30ms, the method `update` is called.

The update method controls the current state of the experiment by using the variables with format `STATE_*`. For example STATE_TRANSFER_TO_DECISION represents the state of the experiment when the subject is showed the cross just before being able to deceide wehther to harvest or to exit the current patch.

The main logic happens through a set ot conditions in the `update` method. A typical state description will be of the form:

    elif self.gstate == Trial.STATE_WAITING_FOR_NEXT_TREE: 
      if (self.justEnteringTheState):
        # what to do when entering the state for the first time

      # what to do every 30 ms
      self.tree.setPosition(ratioTime,self.screen.get_rect().w)     
      # here we move the tree a little bit 

      # finally we test whether we should move to different state
      if ((self.time() > self.generator.d)):
        self.setState(Trial.STATE_TRANSFER_TO_DECISION)  

This file uses two other subcomponent, `treesprites` and `patchgenerator`.

### patchgenerator.py

It contains the description of the environment. For instance it knows the value of the current 
harvest time and travel time. This object also computes the deplated rewards and any
randomness associated with it.  Look at the method `computeReward` to see how this is done.

Among other things, what this file does is load the environment description from the expconf file.

### treesprites.py

This file describes the different objects that needs to be drawn onto the screen. 
Sprite is a pygame terminology and all sprites must comply with the requirements of pygame.

The file for instance contains the following sprites:

 - Tree
 - Apple
 - FixationCross

