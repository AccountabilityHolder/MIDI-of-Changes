import mido
from tqdm import tqdm
import argparse
import sys
import operator
import os
import random
import math
from enum import Enum, IntEnum

class Articulations(Enum):
	NORMAL, STACCATO, TENUTO, PEDAL, REST = range(5)

class MsgPriority(IntEnum):
	NOTE_OFF, NOTE_ON = range(2)

class NoteSequence:
	def __init__(self, quiet = False):
		self.seq = []
		self._silent = quiet #turns off progress bars inside class
		return None



	def addNote(self, pitch, volume, start, end, channel=0):
		#start and end are in absolute time
		#ASSERT 0 <= start <= end <= sys.maxsize
		#ASSERT 0 <= pitch <= 127
		#ASSERT 0 <= volume <= 127
		#ASSERT 0 <= channel <= 15
		note={'start':start,'end':end,'pitch':pitch,'vol':volume,'ch':channel}
		self.seq.append(note)

		return None
	

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
		
		#mido/midi cannot handle delta times greater than this
		maxDeltaTime = 268435455
		
		messages = []
		out = []

		with tqdm(total=len(self.seq),disable=self._silent, \
				  desc='Converting') as pbar:
			for i in self.seq:
				#skip 0-length notes
				if(i['start'] != i['end']):
					messages.extend(NoteSequence._makeAbsTimeMessage(i))

				#throw error if delta time is too high
				if((i['end'] - i['start']) > maxDeltaTime):
					raise ValueError(f"Delta time for message {i} is greater \
than maximum delta time allowable by MIDI 1.0 Standards: \
{i['end']-i['start']} < {maxDeltaTime}")

				pbar.update(1)



		messages.sort(key=operator.itemgetter('absTime','priority'))
		prevTime = 0

		with tqdm(total=len(messages),disable=self._silent,\
				  desc='Writing   ') as pbar:
			for a in messages:
				d = a['data']
				dTime = a['absTime'] - prevTime
				prevTime = a['absTime']

				m = mido.Message(a['message'],channel=d['c'],note=d['n'],\
							 velocity=d['v'],time=dTime)
				out.append(m)

				pbar.update(1)

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



def toCharacter(h):
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



def printHexagrams(hexSeq):
	#hexSeq is a iterable of hexagram dict
	hexString = ''	#UTF-8 hexagrams
	jianti = ''		#UTF-8 simplified characters

	for h in hexSeq:
		hexString += f'{uHexagram(h)} '
		jianti += toCharacter(h)

	print(f'\nYijing Hexagrams:\n{hexString[:-1]}\n\nNames:\n{jianti}')

	return None



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



def _generateNotes(pbar, seq, hexs, cNote, maxTime=0, maxNotes=0, channel=0,\
				   voice=0):
	#needed general variables...
	songCounter = 1
	genNewNote = False
	changesRequired = 4
	
	pedNotes = [] #keep track of which notes are played w/ pedal

	#mido/midi cannot handle delta times greater than this
	maxDeltaTime = 268435455

	usingTime = (maxTime > 0)
	prevNotes = maxNotes

	while((songCounter <= maxTime) or (maxNotes > 0)):

		if(not genNewNote):
			chHex = randomHexagram()

			#end note immediately if we reach the longest note possible in midi
			#this is certainly impossible to occur as it's (2^28 - 1) ticks
			abort = (songCounter - cNote['cSt']) >= maxDeltaTime

			#roll to see if we end the current note
			if(chHex['numChanges'] >= changesRequired or abort):
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

			hexs.extend(generateNote(cNote))

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

		#progress bar handling
		#updates depending on whether generating for [x] notes or [x] ticks
		if(usingTime):
			pbar.update(1)
		elif(prevNotes != maxNotes):
			pbar.update(1)
			prevNotes = maxNotes

		songCounter += 1

	#last update
	pbar.update(1)

	#clean up last note, if necessary
	if (not genNewNote):
		seq.addNote(cNote['cP'],cNote['cV'],cNote['cSt'],songCounter,channel)

	#clean up any remaining pedal notes
	for notes in pedNotes:
		seq.addNote(notes['p'],notes['v'],notes['st'], songCounter, channel)
	return None



def generateVoice(seq, maxTime=0, maxNotes=0, channel=0, voice=0):
	#ASSERT isinstance(seq, NoteSequence())
	#ASSERT (maxTime + maxNotes > 0) and (maxTime == 0 xor maxNotes == 0)
	#ASSERT 0 <= channel <= 15
	#ASSERT 0 <= voice <= 127
	#generates notes and writes to seq for given channel and MIDI program
	#generates until written maxNotes-many notes or elapse maxTime-many ticks
	#returns sequence of (meaningful) hexagrams used to generate sequence
	

	hexSequence = []

	cNote = {'cP':0,'cV':0,'cArt':Articulations.NORMAL,'cSt':0}

	#start our initial note; init. pitch & vol := 29 + random.randrange(64)
	#which gives a uniform distribution from F1 to G#4 centered on middle C
	for i in range(2):
		hexSequence.append(randomHexagram())

	cNote['cP'] = 29 + hexSequence[0]['hexagram']
	cNote['cV'] = 29 + hexSequence[1]['hexagram']

	bDesc = f'Channel {channel:>2}'

	with tqdm(total=max(maxTime,maxNotes),disable=seq._silent,\
			  desc=bDesc) as pbar:
		_generateNotes(pbar,seq,hexSequence,cNote,maxTime,maxNotes,channel,\
					   voice)

	return hexSequence



def setupParser():
	rSeed = random.randrange(sys.maxsize)

	p = argparse.ArgumentParser(prog='./midi_of_changes.py',epilog=\
		'\"Imagine, A sound being \'better!\'\" —John Cage (1912-1992)', \
		description='''\
		Generates a MIDI file using chance operations derived from hexagrams 
		specified in the Book of Changes, 《易经》 (often rendered as 
		"I Ching" in English). Inspired by John Cage's use of hexagrams in 
		composing. The first complete piece composed by Cage in this manner 
		was Music of Changes in 1951.\
		''')
	p.add_argument('-l', '--length', required=True, type=int, help='''\
		int: sets how long the generated midi track will be. Use --units or 
		-u to specify length in seconds, MIDI ticks, or notes. min: 1
		''')
	p.add_argument('-u', '--units', type=str, default='s', \
		choices=('s','sec','t','ticks','n','notes'), help='''\
		str: sets the units for argument -l or --length. Use "s" or "sec" for 
		lengths given in seconds, "t" or "ticks" for lengths given in MIDI 
		ticks, or "n" or "notes" for generating a fixed number of notes per 
		channel. default: "s"\
		''')
	p.add_argument('-t', '--tempo', type=int, default=12, help='''\
		int: sets how frequently a new note is played. On average, a new note 
		occurs every (13.3/t) seconds. min:1, max:32767, default: 12\
		''')
	p.add_argument('-s', '--seed', type=int, default=rSeed, \
				   help=f'''\
		int: sets the seed for the random number generator. min: 0, max: 
		{sys.maxsize}, default: random\
		''')
	p.add_argument('-p', '--program', nargs='+', type=int, default=[1], \
		help='''\
		int(s): takes up to 15 integers specifying the MIDI program to use 
		for each channel. min:1, max:128, default: 1\
		''')
	p.add_argument('--hexagram', action='store_true', help='''\
		include this flag to print all hexagrams used in MIDI generation
		''')
	p.add_argument('--quiet', action='store_true', help='''\
		silences all output. does not override --hexagram flag
		''')

	return p



def validateArgs(args):
	prog = './midi_of_changes.py'
	#confirms arguments given are within reasonable bounds
	if(args.length <= 0):
		raise ValueError(f'{prog}: error: argument -l/--length: out of range \
value: {args.length} (choose a number greater than zero)')

	if(len(args.program) > 15):
		raise ValueError(f'{prog}: error: argument -p/--program: too many \
programs specified: {args.program} (argument takes no more \
than 15 values)')

	for p in range(len(args.program)):
		if (args.program[p] < 1 or args.program[p] > 128):
			raise ValueError(f'{prog}: error: argument -p/--program: out of \
range value: {args.program[p]} at position {p} (choose numbers in 1 — 128)')

	if(args.tempo <= 0 or args.tempo > 32767):
		raise ValueError(f'{prog}: error: argument -t/--tempo: out of range \
value: {args.tempo} (choose a number in 1 — 32767)')

	if(args.seed < 0 or args.seed > sys.maxsize):
		raise ValueError(f'{prog}: error: argument -s/--seed: out of range \
value: {args.seed} (choose number in 0 — {sys.maxsize})')

	return None



def main():

	#argument parsing
	parser = setupParser()
	args = parser.parse_args()
	validateArgs(args)

	if (not args.quiet):
		print(r'''
 +--------------------------------------------------------------------+
 ] 8. .8 "8@8" @@:. "8@8"       .8:   .8@8  8                         [
 ] @8.8@   @   @ "8   @         8 "   8  "8 8                         [
 ] @ 8 @   @   @  @   @    .8. 8@8    @     @8:. :":  8:. .:: :": .": [
 ] @ " @   @   @ .8   @    8 8  8     8  .8 8 "8 .:8  8 8 8 8 8:" "*. [
 ] @   @ .8@8. 8@:" .8@8.  "8"  8     "8@8  8  8 ".8. 8 8 ":8 ".: :." [
 +--------------------------------------------------------. 8---------+
                                                          ":"
		''')

	#turn arguments into variables
	seed = args.seed #random.randrange(sys.maxsize)
	random.seed(seed)
	tpq = args.tempo
		#ticks per quarter note. 1 quarter note = 0.5s (@120bpm)
		#time per tick (seconds) = 1m/120b*60s/1m*1b/tpq = 1/(2*tpq) sec
		#mido cannot change tempo from 120bpm

	voices = [] 
	#MIDI program lists are usually 1-indexed; turn into 0-indexed entries
	for p in args.program:
		voices.append(p-1)

	#determine length depending on units given by user
	if (args.units == 's' or args.units == 'sec'):
		mNotes = 0
		length = 2 * args.length * tpq #seconds into MIDI ticks @120bpm
		fileNameUnits = 't' #filenames are never in terms of seconds
	
	elif (args.units == 't' or args.units == 'ticks'):
		mNotes = 0
		length = args.length
		fileNameUnits = 't'
	
	else:
		mNotes = args.length
		length = 0
		fileNameUnits = 'n'


	#setup variables and housekeeping
	version = '1.0.1'
	usedHexagrams = []
	output = mido.MidiFile(type = 0,ticks_per_beat=tpq)
	song = output.add_track()
	rawNotes = NoteSequence(args.quiet)

	#skip channel 9. it only does percussion
	if(len(voices) >= 10):
		loopRange = list(range(9))+list(range(10,len(voices)+1))
	else:
		loopRange = range(len(voices))

	for i in loopRange:
		if i > 8:
			v = voices[i-1]
		else:
			v = voices[i]
		song.append(mido.Message('program_change',channel=i,program=v))

	if(not args.quiet):
		if(mNotes > 0):
			print(f'Generating a song with {len(voices)} voices \
for {mNotes} note(s)...')
		else:
			print(f'Generating a song with {len(voices)} voices \
for {int(length/2/tpq)} second(s)...')

	#skip channel 9
	for j in loopRange:
		if j > 8:
			v = voices[j-1]
		else:
			v = voices[j]
		usedHexagrams.extend(generateVoice(rawNotes, maxTime = length, \
			maxNotes = mNotes, channel=j, voice=v))

	if(not args.quiet):
		print(f'\nWriting file...')
	midiMessages = rawNotes.generateMessages()

	for m in midiMessages:
		song.append(m)

	song.append(mido.MetaMessage('end_of_track'))

	#get path of script so we can save to ./out/
	outPath = os.path.dirname(__file__)
	outPath += '/out/'
	#generate output subfolder if it does not yet exist
	if not os.path.isdir(outPath):
		os.makedirs(outPath)

	#generate filename based on arguments
	#Two filenames will be equal iff the output should be exactly the same
	fileN = f"v{version}_seed {seed}_tempo {tpq}_"
	if (fileNameUnits == 'n'):
		fileN += f"length {mNotes}n_"
	else:
		fileN += f"length {length}t_"
	fileN += f"programs"
	for v in voices:
		fileN += f" {v}"
	fileN += f".mid"

	if(not args.quiet):
		print(f"\nSaving to:\n{outPath+fileN}")
	output.save(filename = outPath+fileN)

	if(args.hexagram):
		printHexagrams(usedHexagrams)

	return 0



if __name__ == "__main__":
	sys.exit(main())