#!/usr/bin/python

'''
This is a Halloween party script which pauses Spotify and plays a video
at random intervals.
'''

import random
import subprocess
from subprocess import call
from time import sleep
import os
import datetime

start_time = datetime.time(21, 0, 0)
stop_time = datetime.time(23, 0, 0)

video_dir = '/home/alex/Videos/scream/'
videos = { 'scream1_nofade.ogg': 30,
	   'happy.ogg': 1,
	   'evil_laugh.ogg': 5,
	}


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
	print("start<end")
        return start <= x <= end
    else:
	print("end<start")
        return start <= x or x <= end


def weighted_choice(weights):
	total = sum(weights[video] for video in weights)
	r = random.uniform(0, total)
	upto = 0
	print("total: %s\nrandom: %s" % (total, r))

	for video in weights:
		w = weights[video]
		if upto + w > r:
			return video
		upto += w
	assert False, "shouldn't get here"


def spotifyPause():
	command = "dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Pause"
	print("pausing spotify")
	os.system(command)


def spotifyPlay():
	print("playing spotify")
	command = "dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause"
	os.system(command)


def play_video(video_file):
	print("Playing %s" % video_file)
	#call(['/usr/bin/mplayer', '-fs',  video_file], stdout=None, stderr=None)
	#result = subprocess.Popen(['/usr/bin/mplayer', '-really-quiet', '-fs',  video_file])
	result = subprocess.check_call(['/usr/bin/mplayer', '-really-quiet', '-fs',  video_file], stdout=None, stderr=None)
	return result


def playBuzz(buzzfile):
	print("Buzz...")
	result = subprocess.check_call(['/usr/bin/mplayer', '-really-quiet', '-ss', '18', buzzfile], stdout=None, stderr=None)
	return result
	

def infiniteLoop():
	while 1:
		current_time = datetime.datetime.now().time()
		#if current_time > stop_time or current_time < midday:
	
		choice = weighted_choice(videos)

		random_time = random.randrange(1200,2400)
		random_time = 3

		video_file = video_dir + choice
		print("Chose video %s after %s seconds" % (video_file, random_time)) 
		sleep(random_time)

		# Whether to play buzz
		buzz = False
		if random.randrange(0,100) > 90:
			buzz = True

		# Continue if outside time range
		if not time_in_range(start_time, stop_time, current_time):
			print("Not playing video, outside time range")
			continue

		# Do it
		spotifyPause()
		if buzz:
			playBuzz('/home/alex/Videos/scream/audio/buzz.mp3')
		play_video(video_file)
		spotifyPlay()


if __name__ == "__main__":
	infiniteLoop()
