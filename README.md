# MIDI of Changes
MIDI of Changes is a command-line script that generates MIDI files via chance operations. This program derives it's name from the Book of Changes,《易经》(transliterated as "Yijing" or, more often, as "I Ching"). In order to make decisions on how long to play a note and how much to change the pitch and volume of the next note, the program generates hexagrams from the Book of Changes (a vertical sequence of 6 lines, each broken or unbroken; examples found later in this readme) and interprets these in various ways. The use here of Yijing hexagrams to generate music is inspired by composer John Cage (1912–1992) who first began using such hexagrams in his music composition in 1951. His first pieces inspired by the Book of Changes were *Imaginary Landscape No. 4* and *Music of Chages* (both 1951) from which this program also derives its name.

More information on how John Cage used the Yijing hexagrams throughout his career can be found here: https://web.archive.org/web/20240121013848/https://www.biroco.com/yijing/cage.htm (archived 2024-01-24)

## Installation
MIDI of Changes requires Python 3.7 or higher and mido to run
### Ubuntu/Debian
Install Python 3 and pip via the apt package manager using the following in the command-line:
```
sudo apt-get install python3-pip
```
Install mido and tqdm via pip using the following command:
```
pip install mido tqdm
```

### Windows
To install Python 3 and pip, go to http://python.org/downloads, download the latest stable Python release, and install using provided installer.
To open the command line press `Win + R` ( <img height="16" width="16" src="https://unpkg.com/simple-icons@v11/icons/windows10.svg"> + R ) to open the run dialog box, type `cmd.exe` in the textbox, then hit enter.
Install mido and tqdm via pip using the following command in the command line:
```
pip install mido tqdm
```

## Usage
All generated MIDI files are stored in a sub-folder called `out`
### Ubuntu/Debian
To run MIDI of Changes, use the following command in the command-line while in the directory containing the script. Arguments listed below.
```
python3 ./midi_of_changes.py -l SECONDS [...]
```

### Windows
To run MIDI of Changes, use the following command in the command-line while in directory containing the script. Arguments listed below.
```
py ./midi_of_changes.py -l SECONDS [...]
```

## List of Arguments
Following is a list of all arguments the script accepts
### Help `-h or --help`
**(optional)** Displays a help message then exits the program. No files generated.
### Length `-l [x] or --length [x]`
**(required)** Takes a positive integer. Specifies how long the generated MIDI file will be. By default, the script assumes \[x\] is given in seconds. Other possible units are number of notes and raw MIDI ticks (not recommended)
### Units `-u [x] or --units [x]`
**(optional)** Takes a string of characters. Specifies what "units" the number given in the length argument is. Use `s` or `sec` for seconds, `n` or `notes` for number of notes, and `t` or `ticks` for MIDI ticks (not recommended).

Valid strings: `s`, `sec`, `t`, `ticks`, `n`, `notes`.
### Tempo `-t [x] or --tempo [x]`
**(optional)** Takes a positive integer. Specifies how frequently a new note is generated. Tempo is uses arbitrary units, higher numbers produce more notes per second. On average, a new note will be played every `13.3/[x]` seconds in the resultant MIDI file. By default, the script will fill in `12` for `[x]`.

Minimum possible value of `[x]` is 1 and maximum value of `[x]` is 32,767.
### Seed `-s [x] or --seed [x]`
**(optional)** Takes a non-negative integer. Specifies the random number generator seed to use when generating the MIDI file. If two files have the same arguments and the same seed, they will be identical; if two files have the same arguments but different seeds they will (almost always) be different. By default, the script will use a random seed.

Minimum possible value of `[x]` is 0; maximum possible value of `[x]` depends on your computer but will usually be `9223372036854775807` for 64-bit machines.
### Programs (or Instruments) `-p [x ...] or --program [x ...]`
**(optional)** Takes multiple positive integers. Specifies which MIDI instruments to use when generating the MIDI file. Each instrument is generated on its own channel. As MIDI files can only handle up to 16 channels, this argument will only take up to 15 integers because we skip channel 10 (plays percussion instead of notes). By default, the script will use a single `1` for `[x ...]`. 

Minimum possible value of each `[x]` is 1; maximum possible value of `[x]` is 128. List of standard MIDI instruments provided at the end of this document.

For example, for a trumpet duet, use `-p 57 57`. A string quartet could be generated with `-p 41 41 42 43` (two violins, one viola, and one cello).
### Print Hexagrams `--hexagram`
**(optional)** Takes no values. Include this flag to print all hexagrams and names of hexagrams used in generation of the MIDI file. Overrides `--quiet`


Example hexagram output: 
```
~$ python3 ./midi_of_changes.py --seed 0 -l 10 -u notes --hexagram --quiet

Yijing Hexagrams:
䷪ ䷕ ䷒ ䷤ ䷒ ䷣ ䷸ ䷿ ䷭ ䷊ ䷪ ䷠ ䷞ ䷚ ䷜ ䷂ ䷃ ䷾ ䷯ ䷄ ䷞ ䷋ ䷍ ䷜ ䷰ ䷳ ䷴ ䷏ ䷴

Names:
夬贲临家人临明夷巽未济升泰夬遯咸颐坎屯蒙既济井需咸否大有坎革艮渐豫渐
```

### Quiet Output `--quiet`
**(optional)** Takes no values. Include this flag to silence/quiet all console output of the script. Flag `--hexagram` will still print hexagrams to the console if both flags are included
### Example
```~$ python3 ./midi_of_changes.py --seed 1 --length 600 -p 81 81 81```
This command will run the script using a random seed of 1 and will generate a 600 second (10 minute) long song of three synth square waves *(do not include the `~$` if you copy this command).*
## Soft Limits
While most arguments do not have hard upper-bounds, there are values which should not be exceeded. This script is not very memory efficient at large inputs.
**Remember,** command-line scripts can be halted at any time using `Ctrl + C`
### Length
Songs in excess of 86,400 seconds (1 day), 2,073,600 MIDI ticks (1 day at `-t 12`), or 60,000 notes are **not recommended.** At this length, generating each voice uses about 175MB of RAM. Generating the a MIDI using all 15 voices will use 2.5GB of RAM. Storage capacity is not a significant restriction here; a 60,000 note song is approximately 470KB per voice.
### Tempo
Tempos in excess of 256 are **not recommended.** At higher tempos, it may be difficult to distinguish between individual notes and audible artifacting may occur. At a tempo of 256, the shortest notes generated will be 1024th notes (at 120bpm) which last only ~0.977ms.
### Length and Tempo
If you're specifying a non-default tempo (ie. not 12), then the soft limit on the length of the song in seconds will be different. In general, it is not recommended to allow `seconds * tempo` to exceed 1,036,800. For example, at the highest recommended tempo of 256, do not exceed song lengths in excess of 4,050 seconds (67.5 minutes).

## MIDI Program List
| Program Number | Instrument |     |Program Number | Instrument |
| :------------: | :--------: | :-: |:------------: | :--------: |
|1|Grand Piano| |65| Soprano Sax|
|2|Bright Acoustic Piano| |66| Alto Sax|
|3|Electric Grand Piano | |67| Tenor Sax|
|4|Honky-tonk Piano| |68| Baritone Sax|
|5|Electric Piano 1| |69| Oboe|
|6|Electric Piano 2| |70| English Horn|
|7|Harpsichord | |71| Bassoon|
|8|Clavinet | |72| Clarinet|
|9|Celesta | |73| Piccolo|
|10|Glockenspiel | |74| Flute|
|11|Music Box | |75| Recorder|
|12|Vibraphone | |76| Pan Flute|
|13|Marimba | |77| Blown Bottle|
|14|Xylophone | |78| Shakuhachi|
|15|Tubular Bells | |79| Whistle|
|16|Dulcimer | |80| Ocarina|
|17|Drawbar Organ | |81| Lead 1 *(square)*|
|18|Percussive Organ | |82| Lead 2 *(saw)*|
|19|Rock Organ | |83| Lead 3 *(calliope)*|
|20|Church Organ | |84| Lead 4 *(chiff)*|
|21|Reed Organ | |85| Lead 5 *(charang)*|
|22|Accordion | |86| Lead 6 *(voice)*|
|23|Harmonica | |87| Lead 7 *(fifths)*|
|24|Bandoneon | |88| Lead 8 *(bass & lead)*|
|25|Acoustic Guitar *(nylon)* | |89| Pad 1 *(new age)*|
|26|Acoustic Guitar *(steel)*| |90| Pad 2 *(warm)*|
|27|Electric Guitar *(jazz)* | |91| Pad 3 *(polysynth)*|
|28|Electric Guitar *(clean)* | |92| Pad 4 *(choir)*|
|29|Electric Guitar *(muted)* | |93| Pad 5 *(bowed)*|
|30|Electric Guitar *(overdrive)* | |94| Pad 6 *(metallic)*|
|31|Electric Guitar *(distortion)* | |95| Pad 7 *(halo)*|
|32|Electric Guitar *(harmonics)* | |96| Pad 8 *(sweep)*|
|33|Accoustic Bass | |97| FX 1 *(rain)*|
|34|Electric Bass *(finger)* | |98| FX 2 *(soundtrack)*|
|35|Electric Bass *(pick)* | |99| FX 3 *(crystal)*|
|36|Electric Bass *(fretless)* | |100| FX 4 *(atmosphere)*|
|37|Slap Bass 1 | |101| FX 5 *(brightness)*|
|38|Slap Bass 2 | |102| FX 6 *(goblins)*|
|39|Synth Bass 1 | |103| FX 7 *(echoes)*|
|40|Synth Bass 2 | |104| FX 8 *(sci-fi)*|
|41|Violin | |105| Sitar|
|42|Viola | |106| Banjo|
|43|Cello | |107| Shamisen|
|44|Contrabass | |108| Koto|
|45|Tremolo Strings | |109| Kalimba|
|46|Pizzicato Strings | |110| Bag pipe|
|47|Orchestal Harp | |111| Fiddle|
|48|Timpani | |112| Shanai|
|49|String Ensemble 1 | |113| Tinkle Bell|
|50|String Ensemble 2 | |114| Agogo|
|51|Synth Strings 1 | |115| Steel Drumbs|
|52|Synth Strings 2 | |116| Woodblock|
|53|Choir Aahs | |117| Taiko Drum|
|54|Voice Oohs | |118| Melodic Tom|
|55|Synth Voice | |119| Synth Drum|
|56|Orchestra Hit | |120| Reverse Cymbal|
|57|Trumpet | |121| Guitar Fret Noise|
|58|Trombone | |122| Breath Noise|
|59|Tuba | |123| Seashore|
|60|Muted Trumpet | |124| Bird Tweet|
|61|French Horn | |125| Telephone Ring|
|62|Brass Section | |126| Helicopter|
|63|Synth Brass 1 | |127| Applause|
|64|Synth Brass 2 | |128| Gunshot|