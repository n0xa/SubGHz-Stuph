#!/usr/bin/env python2
# YardStick One ASK/OOK Scanner by Noah Axon
# Based on prior work by @AndrewMohawk 
import sys
import time
from rflib import *
import argparse
import bitstring
import re
import operator
import datetime as dt
import select
import tty

keyLen = 0
baudRate = 4800
frequency = 314915000

def ConfigureD(d):
	d.setMdmModulation(MOD_ASK_OOK)
	d.setFreq(frequency)
	d.makePktFLEN(keyLen)
	d.setMdmDRate(results.baudRate)
	d.lowball()
	
	print "[+] Radio Config:"
	print " [-] ---------------------------------"
	print " [-] Modulation: MOD_ASK_OOK"
	print " [-] Start Frequency: ",frequency
	print " [-] Baud Rate:",results.baudRate
	print "[-] ---------------------------------"

parser = argparse.ArgumentParser(description='Simple program to scan for ASK/OOK codes',version="YardStick One ASK/OOK Scanner 1.0 - by Noah Axon")
parser.add_argument('-fa', action="store", default="433000000", dest="startFreq",help='Default: 433000000 | Frequency to start scan at',type=long)
parser.add_argument('-fb', action="store", default="434000000", dest="endFreq",  help='Default: 434000000 | Frequency to end scan at',type=long)
parser.add_argument('-fs', action="store", default="50000", dest="stepFreq",     help='Default: 50000     | Frequency step for scanning',type=long)
parser.add_argument('-ft', action="store", default="1000", dest="timeStepFreq",  help='Default: 1000ms    | Frequency step delay',type=long)
parser.add_argument('-br', action="store", dest="baudRate",default=4800,         help='Default: 4800      | Baudrate to Receive',type=int)
parser.add_argument('-p', action="store", dest="paddingZeros", default=15,       help='Default: 15 | Repeated zeros needed for pattern match',type=int)
parser.add_argument('-ms', action="store", dest="minimumStrength", default=-80,  help='Default: -80dB | Minimum strength',type=int)
parser.add_argument('-ln', action="store", dest="lockNum", default=5,            help='Default: 5 | Minimum codes to receive before locking',type=int)
results = parser.parse_args()

currFreq = results.startFreq;
frequency = currFreq
sys.stdout.write("Configuring RFCat...\n")
d = RfCat()
ConfigureD(d)
allstrings = {}
lens = dict() 
lockOnSignal = True
lockedFreq = False

print "Scanning for ASK/OOK Remotes... Press <enter> to stop or <space> to unlock and continue scanning"

def isData():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

tty.setcbreak(sys.stdin.fileno())

def showStatus():
	strength= 0 - ord(str(d.getRSSI()))
	sigFound = "0"
	if(currFreq in allstrings):
		sigFound = str(len(allstrings[currFreq]))
	sys.stdout.write('\rFreq: [ ' + str(currFreq) + ' ] Strength [ ' + str(strength) + ' ] Signals Found: [ ' + sigFound + ' ]' )
	if(lockedFreq == True):
		sys.stdout.write(" [FREQ LOCKED]")
	sys.stdout.write("      ")
	sys.stdout.flush()

n1=dt.datetime.now()

while True:
	try:
		if isData():
			x= ord(sys.stdin.read(1))
			if (x == 3 or x == 10):
				break
			elif(x == 32):
				print " unlocking";
				currFreq += results.stepFreq
				lockedFreq = False
		y, t = d.RFrecv(1)
		sampleString=y.encode('hex')
		# lets find all the zero's
		showStatus();
		zeroPadding = [match[0] for match in re.findall(r'((0)\2{25,})', sampleString)]
		for z in zeroPadding:
			currLen = len(z)
			if currLen in lens.keys():
				lens[currLen] = lens[currLen] + 1
			else:
				lens[currLen] = 1
		sorted_lens = sorted(lens.items(), key=operator.itemgetter(1), reverse=True)
		lens = dict()
		if(sorted_lens and sorted_lens[0][0] > 0 and sorted_lens[0][0] < 400):
			zeroPaddingString = "0" * sorted_lens[0][0]
			possibleStrings = sampleString.split(zeroPaddingString)
			possibleStrings = [s.strip("0") for s in possibleStrings]
			for s in possibleStrings:
				if(currFreq in allstrings):
					allstrings[currFreq].append(s)
				else:
					allstrings[currFreq] = [s]
				if((len(allstrings[currFreq]) > results.lockNum) and lockOnSignal == True):
					lockedFreq = True

		n2=dt.datetime.now()
		if(((n2-n1).microseconds * 1000) >= results.timeStepFreq):
			if(lockedFreq == False):
				currFreq += results.stepFreq
				if(currFreq > results.endFreq):
					currFreq = results.startFreq
				n1=dt.datetime.now()
				d.setFreq(currFreq)
		
	except KeyboardInterrupt:
		break
	except ChipconUsbTimeoutException:
		pass

sortedKeys = sorted(allstrings, key=lambda k: len(allstrings[k]), reverse=True)

if(len(sortedKeys) > 0):
	print "\nIdentified the following ASK/OOK Keys:"
	for var in range(len(sortedKeys)):
		del sorted_lens
		strings = allstrings[sortedKeys[var]]
		d.setFreq(sortedKeys[var])
		
		for a in strings:
			if len(a) > 1:
				currLen = len(a)
				if currLen in lens.keys():
					lens[currLen] = lens[currLen] + 1
				else:
					lens[currLen] = 1

		sorted_lens = sorted(lens.items(), key=operator.itemgetter(1), reverse=True)
		if len(sorted_lens) > 0:
			searchLen = sorted_lens[0][0]
			foundKeys = []
			for a in strings:
				if(len(a) == searchLen):
					foundKeys.append(bin(int(a,16))[2:])

			maxlen = 0;
			for foundKey in foundKeys:
				if len(foundKey) > maxlen:
					maxlen = len(foundKey)
			for i in range(0,len(foundKeys)):
				if(len(foundKeys[i]) < maxlen):
					foundKeys[i] = foundKeys[i] + ("0" * (maxlen - len(foundKeys[i])))

			finalKey = "";
			for charPos in range(0,maxlen):
				total = 0;
				for i in range(0,len(foundKeys)):
					thisChar = foundKeys[i][charPos]
					total += int(thisChar)
				if(total > (len(foundKeys) / 2)):
					finalKey += "1"
				else:
					finalKey += "0"

			key_packed = bitstring.BitArray(bin=finalKey).tobytes()

			keyLen = len(key_packed)
			if keyLen > 0:
				print "-----------"
				print "[+] Key len:  ",keyLen,""
				print "[+] Key:      ", key_packed.encode('hex')
				print "[+] Freq:     ", str(sortedKeys[var-1])
	sys.stdout.write("\nDone.\n")
	 	
else:
	print "\n\nNo keys found :(\nbye."

d.setModeIDLE()
