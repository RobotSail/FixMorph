# -*- coding: utf-8 -*-

import sys

GREY = '\t\x1b[1;30m'
RED = '\t\x1b[1;31m'
GREEN = '\x1b[1;32m'
YELLOW = '\t\x1b[1;33m'
BLUE = '\t\x1b[1;34m'
ROSE = '\n\t\x1b[1;35m'
CYAN = '\x1b[1;36m'
WHITE = '\t\x1b[1;37m'

debug = False

''' Functions to print (colors, title, presentation of the program...)'''

def color(message, color, jumpline=True):
    with open("output/crochet_log", 'a') as out_file:
        r = "\033[K" + color + str(message) + '\x1b[0m'
        sys.stdout.write(r)
        out_file.write(r)
        if jumpline:
            r = "\n"
            sys.stdout.write("\n")
            out_file.write(r)
        else:
            r = "\033[K\r"
            sys.stdout.write(r)
            out_file.write(r)
        sys.stdout.flush()


def grey(message, jumpline=True):
    color(message, GREY, jumpline)
   
   
def red(message):
    color(message, RED)


def green(message):
    color(message, GREEN)


def yellow(message):
    color(message, YELLOW)


def blue(message):
    color(message, BLUE)
    
    
def rose(message):
    color(message, ROSE)
    
    
def cyan(message):
    color(message, CYAN)


def white(message):
    color(message, WHITE)
      
      
def start():
    cyan("\n\n" + "#"*150 + "\n\n\tStarting PatchWeave...\n\n" + "#"*150)
    cyan("_"*150 + "\n\n" +
    '''
    Crochet was developed by researchers at NUS Tsunami Team:
    
    \tRidwan Shariffdeen (rshariffdeen@gmail.com)
        
    \tPedro Bahamondes (pibahamondesw@gmail.com)
        
    \tShin Hwei Tan (shinhwei0131@gmail.com)
    
    Special Thanks:
        
    \tDr. Abhik Roychoudhury (abhik@comp.nus.edu.sg)
    
    \tAndrew Santosa (dcsandr@nus.edu.sg)
    
    Acknowledgements:
    
    \tThis software uses the following software developped by third parties:
    
    \t\tDeckard (at tools/Deckard). See https://github.com/skyhover/Deckard/
    \t\tfor more info.
    
    \t\tClang (at tools/bin) and some subprojects.
    
    \t\tClang-diff, a tool based on Gumtree diff
    '''
    +"\n" + "_"*150 + "\n")


def exit_msg(runtime, initialization_duration, clone_detection_duration, transplantation_duration):
    green("Time duration for:\n")
    yellow("Initialization: " + initialization_duration)
    yellow("Clone Detection: " + clone_detection_duration)
    yellow("Transplantation: " + transplantation_duration)
    rose("PatchWeave finished successfully after " + runtime + "seconds.\n")

      
def title(title):
    green("_"*150 + "\n\n\t" + title + "\n" + "_"*150+"\n")

def sub_title(sub_title):
    green("\n\t" + sub_title + "\n\t" + "-"*140+"\n")
    
def conditional(message, *args):
    if debug:
        for i in args:
            if not i:
                return None
        white(message)