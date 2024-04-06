import mido
import argparse
import sys
import operator
import random
import math
from enum import Enum, IntEnum

class Articulations(Enum):
	NORMAL, STACCATO, TENUTO, PEDAL, REST = range(5)

class MsgPriority(IntEnum):
	NOTE_OFF, NOTE_ON = range(2)

class NoteSequence:
	def __init__(self):
		self.seq = []
		#self.channels = channels



	def addNote(self, pitch, volume, start, end, channel=0):
		#start and end are in absolute time
		#ASSERT 0 <= start <= end <= sys.maxsize
		#ASSERT 0 <= pitch <= 127
		#ASSERT 0 <= volume <= 127
		#ASSERT 0 <= channel <= 15
		note={'start':start,'end':end,'pitch':pitch,'vol':volume,'ch':channel}
		self.seq.append(note)
	

	@staticmethod
	def _makeAbsTimeMessage(note):
		#note is the dictionary used in List self.seq
		#returns tuple of Mido-like messages in absolute time, not delta time

		n = note['pitch']
		v = note['vol']
		c = note['ch']
		onOffData = {'n':n,'v':v,'c':c}

		msgOn = {'message':'note_on','priority':MsgPriority.NOTE_ON, \
				 'data':onOffData, 'absTime':note['start']}
		msgOff = {'message':'note_off','priority':MsgPriority.NOTE_OFF, \
				  'data':onOffData.copy(), 'absTime':note['end']}

		return (msgOff, msgOn)



	def generateMessages(self):
		#generates and returns a list of mido.Message objects based on the
		#notes given to this object. List is sorted for directly adding to a
		#midi track, assuming NoteSequence holds all notes in a track
		
		messages = []
		out = []

		for i in self.seq:
			#skip 0-length notes
			if(i['start'] != i['end']):
				messages.extend(NoteSequence._makeAbsTimeMessage(i))

		messages.sort(key=operator.itemgetter('absTime','priority'))
		prevTime = 0

		for a in messages:
			d = a['data']
			dTime = a['absTime'] - prevTime
			prevTime = a['absTime']

			m = mido.Message(a['message'],channel=d['c'],note=d['n'],\
							 velocity=d['v'],time=dTime)
			out.append(m)

		return out



def binToKingWen(binaryRepr):
	#ASSERT 0 <= binaryRepr <= 63
	#converts raw hexagram binary representation to King Wen sequence number
	kingWenSequence = (2,24,7,19,15,36,46,11,16,51,40,54,62,55,32,34,8,3,29,60\
		,39,63,48,5,45,17,47,58,31,49,28,43,23,27,4,41,52,22,18,26,35,21,64,38\
		,56,30,50,14,20,42,59,61,53,37,57,9,12,25,6,10,33,13,44,1)
	return(kingWenSequence[binaryRepr])



def kingWenToBin(wen):
	#ASSERT 1 <= wen <= 64
	#converts King Wen sequence number to binary representation
	#King Wen goes from 1 to 64
	binaryRepr = (None,63,0,17,34,23,58,2,16,55,59,7,56,61,47,4,8,25,38,3,48,\
		41,37,32,1,57,39,33,30,18,45,28,14,60,15,40,5,53,43,20,10,35,49,31,62,\
		24,6,26,22,29,46,9,36,52,11,13,44,54,27,50,19,51,12,21,42)
	return(binaryRepr[wen])



def toCharacter(h, kingWen = True):
	#h is a hexagram dict
	#returns simplified chinese characters(s) associated w/ each hexagram

	characters = ("null","乾","坤","屯","蒙","需","讼","师","比","小畜","履","泰","否"\
		,"同人","大有","谦","豫","随","蛊","临","观","噬嗑","贲","剥","复","无妄"\
		,"大畜","颐","大过","坎","离","咸","恒","遯","大壮","晋","明夷","家人","睽"\
		,"蹇","解","损","益","夬","姤","萃","升","困","井","革","鼎","震","艮"\
		,"渐","归妹","丰","旅","巽","兑","涣","节","中孚","小过","既济","未济")
	return characters[h['wen']]



def uHexagram(h):
	#h is a hexagram dict
	#spits out the UTF-8 encoded unicode character for a hexagram
	#(eg. '䷀' for 63 [1 in King Wen sequence])

	return chr(0x4dbf + h['wen'])



def makeHexagram(h, binChanges=0, kingWen=False):
	#ASSERT 0 <= h <= 63 iff !kingWen; 1 <= h <= 64 iff kingWen
	#ASSERT 0 <= binChanges <= 63
	#makes a specified hexagram dictionary and returns to user
	if (kingWen):
		binary = binToKingWen()
		wen = h
	else:
		binary = h
		wen = binToKingWen(h)

	#count the 1s in the binary rep of binChanges
	numC = 0
	b = binChanges
	while(b > 0):
		if(b%2 == 1):
			numC += 1
		b = b >> 1

	return {'hexagram':binary,'wen':wen,'changes':binChanges,'numChanges':numC}




def randomHexagram():
	#generates a random Hexagram according to standard divination probabilities
	#also tracks which lines are changing
	changes = 0
	hexagram = 0
	
	for n in range(6):
		line = random.randrange(2)
		hexagram += line << n
		changeRoll = random.uniform(0,1)
		
		if(line == 0 and changeRoll < 0.125):
			changes += 1 << n
		elif(line == 1 and changeRoll < 0.375):
			changes += 1 << n

	return makeHexagram(hexagram, changes)



def changeArticulation(h):
	#h is a hexagram dict
	#returns whether the next note is a rest or what articulation to change to
	s = Articulations.STACCATO
	t = Articulations.TENUTO
	p = Articulations.PEDAL
	r = Articulations.REST
	arts = (0,r,0,p,t,s,p,s,\
			0,r,0,0,0,s,r,r,\
			0,0,0,t,r,0,0,r,\
			t,r,0,t,0,0,r,0,\
			s,r,0,r,r,0,r,0,\
			0,s,r,0,r,0,0,0,\
			r,0,0,0,0,t,0,t,\
			r,t,0,0,s,s,0,0  )
	return arts[h['hexagram']]



def changePitch(h):
	#h is a hexagram dict
	#returns the delta to change the pitch by
	dPitch = (  0, -3,  7,  0, -8, -9,  2,  0,\
				2, -4,  3, -3,  8, -6,  0,  1,\
				0,  0,  0,  0,  0,  0,  9,  0,\
				1,  0, -7,  6,  5,  0,  0,  6,\
			  -10,  0, 10, -8,  0, -1,  7,-11,\
			   11,-12,  0,  0, -6,  4,  0, -5,\
				0,  8, -4,  0,  3, -2,  5,  4,\
				0,  0, -2,  0, -1, -5, -7, 12  )
	return dPitch[h['hexagram']]



def changeVolume(h):
	#h is a hexagram dict
	#returns the delta to change volume by
	dVol = (  0,  0,  0,  0,  0,  0,  8,  0,\
			  0,-16,  0,  0,  0,  0,  0,  0,\
			  0,  0,  0,  0,  0,  0,  0, 16,\
			  0,  0,-16,  0,  0,  0,  0,  0,\
			  0,  0,  0,-32,  0,  0,  0,  0,\
			 16,  0,  0,  0,  0, 32,  0,  0,\
			  0,  0,  0,  0,  0,  0,  0,  0,\
			 -8,  0,  0,  0,  0,  0,  0,  0  )
	return dVol[h['hexagram']]



def timeEndNote(nStart, cTime, art):
	#PEDAL is handled elsewhere
	dStaccatoRatio = 0.5
	dTenuto = 0
	dNorm = 2
	end = cTime

	if 	 (art == Articulations.NORMAL):
		end = max(nStart + 1, end - dNorm)
	elif (art == Articulations.STACCATO):
		end = max(nStart + 1, math.floor((end-nStart)*dStaccatoRatio + nStart))
	elif (art == Articulations.TENUTO):
		end = max(nStart + 1, end - dTenuto)

	return end



def generateNote(cNote):
	hexSequence = []
	minVol = 8

	#change articulations
	hexSequence.append(randomHexagram())
	nArt = changeArticulation(hexSequence[0])
	if(nArt != 0):
		cNote['cArt'] = nArt

	#generate the new note if we're not resting
	if(cNote['cArt'] != Articulations.REST):
		hexSequence.append(randomHexagram())
		hexSequence.append(randomHexagram())
		cNote['cP'] += changePitch(hexSequence[-2])
		cNote['cV'] += changeVolume(hexSequence[-1])

		cNote['cP'] = min(max(0,cNote['cP']),127)
		cNote['cV'] = min(max(minVol,cNote['cV']),127)

	return hexSequence
	


def generateVoice(seq, maxTime=0, maxNotes=0, channel=0, voice=0):
	#ASSERT isinstance(seq, NoteSequence())
	#ASSERT (maxTime + maxNotes > 0) and (maxTime == 0 xor maxNotes == 0)
	#ASSERT 0 <= channel <= 15
	#ASSERT 0 <= voice <= 127
	#generates notes and writes to seq for given channel and MIDI program
	#generates until written maxNotes-many notes or elapse maxTime-many ticks
	#returns sequence of (meaningful) hexagrams used to generate sequence
	
	#needed general variables...
	hexSequence = []
	songCounter = 1
	genNewNote = False
	changesRequired = 4

	cNote = {'cP':0,'cV':0,'cArt':Articulations.NORMAL,'cSt':0}
	pedNotes = [] #keep track of which notes are played w/ pedal

	#start our initial note; init. pitch & vol := 29 + random.randrange(64)
	#which gives a uniform distribution from F1 to G#4 centered on middle C
	for i in range(2):
		hexSequence.append(randomHexagram())

	cNote['cP'] = 29 + hexSequence[0]['hexagram']
	cNote['cV'] = 29 + hexSequence[1]['hexagram']

	while((songCounter <= maxTime) or (maxNotes > 0)):

		if(not genNewNote):
			chHex = randomHexagram()

			#roll to see if we end the current note
			if(chHex['numChanges'] >= changesRequired):
				genNewNote = True

				cEnd = timeEndNote(cNote['cSt'], songCounter, cNote['cArt'])
				
				if (cNote['cArt'] == Articulations.PEDAL):
					pedNotes.append({'p':cNote['cP'], 'v':cNote['cV'], \
									 'st':cNote['cSt']})
				elif(cNote['cArt'] != Articulations.REST):
					seq.addNote(cNote['cP'], cNote['cV'], cNote['cSt'], \
								cEnd, channel)

				if(cNote['cArt'] != Articulations.REST):
					maxNotes -= 1

				else:
					#reset articulation to normal after a rest
					cNote['cArt'] = Articulations.NORMAL

				#start next note on current step
				cNote['cSt'] = songCounter

		#break if we ran out of notes or time
		if(maxNotes <= 0 and (songCounter > (maxTime - 1))):
			break

		if genNewNote:
			genNewNote = False
			prevArt = cNote['cArt']

			hexSequence.append(generateNote(cNote))

			#if we let go of pedal, end all pedal notes now and clear list
			if(prevArt == Articulations.PEDAL and prevArt != cNote['cArt']):
				for note in pedNotes:
					seq.addNote(note['p'], note['v'], note['st'], songCounter)
				pedNotes = []

			#if same pitch is in pedal notes, end matching note and remove
			#there should be AT MOST one copy of any single pitch in pedNotes
			if(len(pedNotes) > 0):
				i = 0
				while i < len(pedNotes):
					n = pedNotes[i]
					if(n['p'] == cNote['cP']):

						seq.addNote(n['p'], n['v'], n['st'], songCounter)
						pedNotes.pop(i)

						break
					i += 1

		songCounter += 1
		
	#clean up last note, if necessary
	if (not genNewNote):
		seq.addNote(cNote['cP'],cNote['cV'],cNote['cSt'],songCounter,channel)

	#clean up any remaining pedal notes
	for notes in pedNotes:
		seq.addNote(notes['p'],notes['v'],notes['st'], songCounter, channel)

	return hexSequence




def main():
	#setup variables
	version = '0.1.0'
	seed = 128 #random.randrange(sys.maxsize)
	length = 8
	voices = [0, 0]
	tpq = 12 #ticks per quarter note. 1 quarter note = 0.5s (@120bpm)
			 #time per tick (seconds) = 1m/120b*60s/1m*1b/tpq = 1/(2*tpq) sec

	#housekeeping
	random.seed(seed)
	output = mido.MidiFile(type = 0,ticks_per_beat=tpq)
	song = output.add_track()
	rawNotes = NoteSequence()

	for i in range(len(voices)):
		song.append(mido.Message('program_change',channel=i,program=voices[i]))

	for j in range(len(voices)):
		generateVoice(rawNotes, maxNotes = length, channel=j, voice=voices[j])

	messages = rawNotes.generateMessages()

	for m in messages:
		song.append(m)

	fileN = f"{version}_{seed}_{tpq}_{length}"
	for v in voices:
		fileN += f"_{v}"
	fileN += f".mid"

	print(f"\nSaving to: {fileN}")
	output.save(filename = fileN)

	return 0



if __name__ == "__main__":
	sys.exit(main())