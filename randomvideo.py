#!/usr/bin/python

import random
import subprocess
from subprocess import call
from time import sleep
import os
import datetime

start_time = datetime.time(21, 0, 0)
stop_time = datetime.time(23, 30, 0)

video_dir = '/home/alex/Videos/scream/'
videos = { 'scream1_nofade.ogg': 20,
	   'happy.ogg': 1,
	   'evil_laugh.ogg': 5,
	}

def play_video(video_file):
	#call(['/usr/bin/mplayer', '-fs',  video_file], stdout=None, stderr=None)
	#result = subprocess.Popen(['/usr/bin/mplayer', '-really-quiet', '-fs',  video_file])
	result = subprocess.check_call(['/usr/bin/mplayer', '-really-quiet', '-fs',  video_file])


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
	command = "dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause"
	os.system(command)


def infiniteLoop():
	while 1:
		current_time = datetime.datetime.now().time()
		midday = datetime.time(12,0,0)

		if current_time > stop_time or current_time < midday:
			print("Stopping as it's late")
			raise SystemExit 
	
			
		choice = weighted_choice(videos)

		random_time = random.randrange(1200,2400)
		random_time = 3

		if current_time < start_time:
			print("Waiting, too early")
		else:
			video_file = video_dir + choice
			print("Playing %s after %s seconds" % (video_file, random_time)) 
			sleep(random_time)

			spotifyPause()
			play_video(video_file)
			spotifyPlay()


if __name__ == "__main__":
	infiniteLoop()
