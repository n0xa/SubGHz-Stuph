#!/usr/bin/env python2
# YardStick One ASK/OOK Scanner by Noah Axon
# Based on prior work by @AndrewMohawk 
import codecs
import argparse
from rflib import *

inputfile = ''
outputfile = ''

parser = argparse.ArgumentParser(description='Simple program to transmit ASK/OOK codes',version="YardStick One ASK/OOK Transmitter 1.0 - by Noah Axon")
parser.add_argument('-f', action="store", default="433920000", dest="frequency",help='Default: 433920000 | Frequency to transmit on',type=long)
parser.add_argument('-b', action="store", dest="baud",default=4800, help='Default: 4800 | Baudrate to Receive',type=int)
parser.add_argument('-r', action="store", dest="repeat", default=15, help='Default: 15 | Number of times to repeat transmit',type=int)
parser.add_argument('-d', action="store", dest="data", required=True, help='Default: nil | Hex data string to transmit')
results = parser.parse_args()

d = RfCat()
d.setMdmModulation(MOD_ASK_OOK)
d.setFreq(results.frequency)
d.setMdmDRate(results.baud)
ook=codecs.decode(results.data, 'hex')
d.makePktFLEN(len(ook))
for tx in range(0,results.repeat):
    d.RFxmit(ook)
d.setModeIDLE()