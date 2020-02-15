import midi
import numpy as np
import cv2
import note

def is_note_on(event):
    velocity = event.data[1]
    return event.name == "Note On" and velocity > 0


def read_midi(filename):
    """
    Returns a list of tracks.
    Each track is list containing 128 lists of notes.
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
    create_video(note_tracks)






def create_video(note_tracks):
    resolution_x = 1920
    resolution_y = 1080
    frame_rate = 30.0
    waiting_time_before_end = 5.0
    start_time = -0.5
    time_before_current = 2.0
    time_after_current = 14.0

    dt = 1.0 / frame_rate
    end_time = 32.0
    time = start_time


    current_note_indices = [ [0 for i in range(128)] for k in range(len(note_tracks))]
    frames = []
    while time < end_time:
        time_left = time - time_before_current
        time_right = time + time_after_current

        current_notes = []
        for track_index, track in enumerate(note_tracks):
            for pitch_index in range(128):
                min_note_index = current_note_indices[track_index][pitch_index]
                max_note_index = len(track[pitch_index])
                for note_index in range(min_note_index, max_note_index):
                    note = track[pitch_index][note_index]
                    if note.end_time < time_left:
                        current_note_indices[track_index][pitch_index] += 1
                    elif note.start_time < time_right:
                        current_notes.append(note)
                    else:
                        break


        img = create_image(current_notes, time, time_left, time_right)
        frames.append(img)
        time += dt
        print(time)

    # write to file
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    ending = ".avi"
    ending = ".mp4"
    out = cv2.VideoWriter("./output/result" + ending, fourcc, frame_rate, (resolution_x, resolution_y))
    for f in frames:
        out.write(f)
    out.release()




def create_empty_image(size_x=1920, size_y=1080):
    """
    This returns the array on which will be drawn.
    """
    img = np.array([12,12,12], dtype=np.uint8) * np.ones((size_y,size_x,3), dtype=np.uint8)* np.ones((size_y, size_x,1), dtype=np.uint8)
    return img


def create_image(current_notes, time, time_left, time_right):
    minimum_pitch = 30
    maximum_pitch = 80
    y_offset = 40
    resolution_x = 1920
    resolution_y = 1080
    time_before_current = 2.0
    time_after_current = 14.0

    img = create_empty_image()


    no_of_rows = maximum_pitch - minimum_pitch + 1
    row_height = (resolution_y - 2.0 * y_offset) / no_of_rows
    pixels_per_second = resolution_x / (time_before_current + time_after_current)


    x_length_ausgleich = 4.0
    # add notes
    note_y_scale = 0.5
    for note in current_notes:
        velocity = note.velocity

        note_height = row_height * note_y_scale
        note_pos_y_offset = -0.5 * (row_height - note_height) * 2.0

        pitch = note.pitch
        row_no = pitch - minimum_pitch
        y_pos = resolution_y - y_offset - (row_no + 1) * row_height - note_pos_y_offset
        x_pos = (note.start_time - time_left) * pixels_per_second
        x_length = (note.end_time - note.start_time) * pixels_per_second - x_length_ausgleich


        x_pos = int(round(x_pos))
        y_pos = int(round(y_pos))
        x_length = int(round(x_length))
        note_height = int(round(note_height))
        p1 = (x_pos,y_pos)
        p2 = (x_pos+x_length,y_pos+note_height)
        note_color = (0,244,45)
        if is_note_active(note, time):
            note_color = (0,0,245)
        cv2.rectangle(img,p1,p2,note_color,-1)


    # cv2.imshow("test", img)
    # cv2.waitKey(1)
    return img


def is_note_active(note, time):
    if note.start_time < time and note.end_time >= time:
        return True
    else:
        return False




if __name__ == '__main__':
    main()
