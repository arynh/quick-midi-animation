# quick-midi-animation
Convert a MIDI file into a piano-roll animation.
An example can be found in my [YouTube video](#).

## Requirements
* The MIDI file should not contain any changes of the global tempo parameter.
Otherwise, the animation will be out of sync.
* The MIDI file should not contain overlapping notes as this might lead to unsatisfying results.
* You need [Python MIDI](https://github.com/vishnubob/python-midi) to read the MIDI files.


## Usage
* The most important parameters are defined in options.cfg. The path to your MIDI must be provided here.
* Run `python main.py`
