import numpy as np
import cv2
import subprocess
import sys
import shutil
import os

import midi
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


def delete_and_create_folders():
    foldernames = ["./output", "./temp_images"]
    for f in foldernames:
        if os.path.isdir(f):
            shutil.rmtree(f)
        os.mkdir(f)


def main():
    delete_and_create_folders()

    note_tracks, tempo_bpm, resolution = read_midi("test.mid")
    calculate_note_times(note_tracks, tempo_bpm, resolution)
    create_video(note_tracks)
    shutil.rmtree("./temp_images")


def get_maximum_time(note_tracks):
    maximum_time = -999999.9
    for t in note_tracks:
        for pitch_list in t:
            if pitch_list != []:
                if pitch_list[-1].end_time > maximum_time:
                    maximum_time = pitch_list[-1].end_time
    return maximum_time


def get_pitch_min_max(note_tracks):
    pitch_min = 128
    pitch_max = 0
    for t in note_tracks:
        for pitch_list in t:
            for note in pitch_list:
                pitch = note.pitch
                if pitch > pitch_max:
                    pitch_max = pitch
                if pitch < pitch_min:
                    pitch_min = pitch
    return pitch_min, pitch_max


def print_progress(msg, current, total):
    """
    This keeps the output on the same line.
    """
    text = "\r" + msg + " {:9.1f}/{:.1f}".format(current, total)
    sys.stdout.write(text)
    sys.stdout.flush()



def create_video(note_tracks):
    resolution_x = 1920
    resolution_y = 1080
    frame_rate = 25.0
    waiting_time_before_end = 5.0
    start_time = -1.0
    time_before_current = 4.0
    time_after_current = 25.0

    pitch_min, pitch_max = get_pitch_min_max(note_tracks)



    dt = 1.0 / frame_rate
    end_time = get_maximum_time(note_tracks) + waiting_time_before_end
    time = start_time


    current_note_indices = [ [0 for i in range(128)] for k in range(len(note_tracks))]
    img_index = 0
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


        img = create_image(current_notes, time, time_left, time_right, time_before_current, time_after_current, pitch_min, pitch_max)
        cv2.imwrite("./temp_images/%08i.png" % img_index, img)
        time += dt
        img_index += 1
        print_progress("Current time:", time, end_time)
    print("")
    run_ffmpeg(frame_rate, resolution_x, resolution_y)


def run_ffmpeg(frame_rate, resolution_x, resolution_y):
    call_list = []
    call_list.append("ffmpeg")
    call_list.append("-r")
    call_list.append("{:d}".format(frame_rate))
    call_list.append("-f")
    call_list.append("image2")
    call_list.append("-s")
    call_list.append("{:d}x{:d}".format(resolution_x, resolution_y))
    call_list.append("-i")
    call_list.append("./temp_images/%08d.png")
    call_list.append("-vcodec")
    call_list.append("libx264")
    call_list.append("-crf")
    call_list.append("25")
    call_list.append("-pix_fmt")
    call_list.append("yuv420p")
    call_list.append("./output/final.mp4")
    subprocess.call(call_list)


def create_empty_image(bg_color, size_x=1920, size_y=1080):
    """
    This returns the array on which will be drawn.
    """
    img = np.array(bg_color, dtype=np.uint8) * np.ones((size_y,size_x,3), dtype=np.uint8)* np.ones((size_y, size_x,1), dtype=np.uint8)
    return img




def create_image(current_notes, time, time_left, time_right, time_before_current, time_after_current, pitch_min, pitch_max):
    y_offset = 20
    resolution_x = 1920
    resolution_y = 1080
    color_active = (204,153,255)
    color_silent = (102,0,204)
    bg_color = (0,0,0)
    pixels_to_remove_from_notes_x = 4.0
    pixels_to_remove_from_notes_y = 4.0

    img = create_empty_image(bg_color)

    no_of_rows = pitch_max - pitch_min + 1
    row_height = (resolution_y - 2.0 * y_offset) / no_of_rows
    pixels_per_second = resolution_x / (time_before_current + time_after_current)
    note_height = max(1, row_height - pixels_to_remove_from_notes_y)
    note_pos_y_offset = 0.5 * (row_height - note_height)
    for note in current_notes:
        row_no = note.pitch - pitch_min
        y_pos = resolution_y - y_offset - (row_no + 1) * row_height + note_pos_y_offset
        x_pos = (note.start_time - time_left) * pixels_per_second
        x_length = (note.end_time - note.start_time) * pixels_per_second - pixels_to_remove_from_notes_x

        x_pos = int(round(x_pos))
        y_pos = int(round(y_pos))
        x_length = int(round(x_length))
        note_height = int(round(note_height))
        p1 = (x_pos,y_pos)
        p2 = (x_pos+x_length,y_pos+note_height)

        if is_note_active(note, time):
            note_color = color_active
        else:
            note_color = color_silent
        cv2.rectangle(img,p1,p2,note_color,-1)
    return img


def is_note_active(note, time):
    if note.start_time < time and note.end_time >= time:
        return True
    else:
        return False


if __name__ == '__main__':
    main()
