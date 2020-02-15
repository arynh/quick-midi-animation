import midi
import note

def is_note_on(event):
    velocity = event.data[1]
    return event.name == "Note On" and velocity > 0



def read_midi(filename):
    """
    Create tracks containing Note objects.
    The start and end times of the notes are not yet calculated;
    this is done separately.
    """
    midi_tracks = midi.read_midifile(filename)
    resolution = midi_tracks.resolution
    tempo_bpm = 120.0  # may be changed repeatedly in the loop
    note_tracks = []
    for t_index, t in enumerate(midi_tracks):
        notes_pitchwise = [[] for i in range(128)]
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                pitch = elem.data[0]
                if is_note_on(elem):
                    n = note.Note(
                        velocity=elem.data[1],
                        pitch=pitch,
                        start_ticks=total_ticks,
                        track=t_index)
                    notes_pitchwise[pitch].append(n)
                else:
                    for n in reversed(notes_pitchwise[pitch]):
                        if not n.finished:
                            n.end_ticks = total_ticks
                            n.finished = True
                        else:
                            break
            elif elem.name == "Set Tempo":
                tempo_bpm = elem.get_bpm()
        note_tracks.append(notes_pitchwise)
    return note_tracks, tempo_bpm, resolution

def calculate_note_times(note_tracks, tempo_bpm, resolution):
    for t in note_tracks:
        for pl in t:
            for n in pl:
                n.calculate_start_and_end_time(tempo_bpm, resolution)



def main():
    note_tracks, tempo_bpm, resolution = read_midi("test.mid")
    calculate_note_times(note_tracks, tempo_bpm, resolution)






if __name__ == '__main__':
    main()
