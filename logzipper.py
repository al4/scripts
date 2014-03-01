#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
(Note: This script proved to have significant problems in production and the
approach was abandoned. I'm publishing this because it was an interesting
exercise!)
'''

'''
Python script to compress a log directory on the fly.

The process will list files in the directory in sorted order and process them
one by one. For each file it sets an inotify watch, and if there are any events
after reading the file it will wait up to 5 seconds for more data.

Requires argparse (python-argparse in debian), and inotifyx (python-inotifyx).

Run logzipper -h for usage info.
'''

import io
import os
import time
from time import sleep
import inotifyx
import subprocess
import re
import logging
import logging.handlers
import signal
import argparse

## Config variables
# Regex whitelist to match files on. Only files that match one of the regexes
# in this array are processed.
fileRegexes = ['^[0-9]{4}\.log$']


def logSetup(logLevel):
    logger = logging.getLogger("logzipper")

    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logLevel)
    logFormatter = logging.Formatter("%(levelname)s - %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    ch.setFormatter(logFormatter)

    logger.addHandler(ch)

    return logger


def listFiles(sourceDirectory, fileRegexes):
    # This function recursively lists all files in a directory.
    # Returns an array of absolute paths

    fileList = []
    for (path, dirs, files) in os.walk(sourceDirectory):
        for f in files:
            # Check that this file is legit by checking it against our regexes
            for r in fileRegexes:
                if re.search(r, f):  # Only add if matches regex
                    # If filename matches, add path to string and append
                    fileList.append('%s/%s' % (path, f))
                    # Must break out of the regex for-loop to avoid adding more
                    # than once
                    break
    fileList.sort()
    return fileList


def currentFile(inputFile, watchDescriptor):
    # Checks whether inputFile is the current log file.
    # watchDescriptor should be the file descriptor returned by inotifyx.init()
    # Returns True/False

    events = inotifyx.get_events(watchDescriptor, 1)
    logger.debug("IN events: %s" % (len(events)))
    for e in events:
        logger.debug("Event: %s" % e.mask)

    if len(events) >= 1:
        # There were writes, assume current
        logger.debug("currentFile True")
        return True
    else:
        logger.debug("currentFile False")
        return False


def nextFile(inputFile):
    # This function takes the input files and returns the next file in
    # sequence, or None if it doesn't exist. An absolute path is expected.

    logger.debug("Calculating next file after %s" % inputFile)

    # Get the directory and file name
    pathArray = inputFile.split("/")
    thisFile = pathArray[-1].split(".")[0]  # strip extension
    thisDir = pathArray[-2]

    if len(thisFile) != 4:
        logger.error("Time string in file name is > 4")
        raise SystemExit

    logger.debug("Parsed old file :: dir: %s, file: %s" % (thisDir, thisFile))

    try:
        # Convert our directory structure to unixtime (i.e. seconds since epoc)
        fileDay = int(thisDir) * 86400           # the dir is days since epoc
        fileHour = int(thisFile[0:2]) * 3600     # add hours
        fileMinute = int(thisFile[2:4]) * 60     # add the minute
    except ValueError:
        logger.error("Could not parse time stamp for file %s, check directory "
                     "structure" % inputFile)
        raise SystemExit

    logger.debug("Calculted time values :: day: %s, hour: %s, min: %s" % (
        fileDay, fileHour, fileMinute))

    # Our file's minute in unixtime
    fileTime = fileDay + fileHour + fileMinute

    # Calculate the file name and path of the next file by adding 60 seconds
    newFileTime = int(fileTime) + 60
    newFileDir = int(newFileTime / 86400)
    newFileName = time.strftime('%H%M', time.localtime(newFileTime))

    # Replace values in array and build new string
    pathArray[-1] = str(newFileName).zfill(4) + ".hits"
    pathArray[-2] = str(newFileDir)
    newFilePath = "/".join(pathArray)

    # logger.debug("Old file: " + inputFile)
    # logger.debug("New file: " + newFilePath)

    try:
        with open(newFilePath):
            pass
    except IOError:
        logger.error(newFilePath + " doesn't exist")
        return None

    return newFilePath


def xzCompress(inputFile, outputFile):
    # Compresses a file, that may be actively written to, with xz.
    # Returns the file name on success, or None on failure

    # command uses custom streaming build of xz
    xzCommand = "export LD_LIBRARY_PATH=/usr/local/lib; /usr/local/bin/xz2 -z1 > %s" % (outputFile)
    # xzCommand = "/usr/local/bin/xz -z1 | pv -B 1024 -L 100 > %s" % (outputFile)

    IN_WATCH_EVENTS = inotifyx.IN_MODIFY

    try:
        # Sets up the main inotify watcher
        fd = inotifyx.init()
        watcher = inotifyx.add_watch(fd, inputFile, IN_WATCH_EVENTS)
        with io.open(inputFile, mode='r+b') as fileStream:
            # Loop until no more data
            try:
                xzp = subprocess.Popen(
                    xzCommand, stdin=subprocess.PIPE, shell=True,
                    close_fds=False, preexec_fn=subprocessSetup)

                # Counter for retrys
                trycount = 0
                while 1:
                    # Main loop which reads the file and writes to xz stdin
                    data = fileStream.read(1024000)
                    current = False
                    # Assume reading a normal file until we get to the end

                    if len(data) == 0:
                        current = currentFile(inputFile, fd)
                        if not current:
                            # Reached EOF, check next file exists
                            sleep(0.1)  # Prevent race condition

                            if nextFile(inputFile) is not None:
                                logger.debug("Breaking, next file exists!")
                                break

                            trycount += 1
                            logger.debug("Waiting for next file or more data.."
                                         + str(trycount))
                            sleep(1)

                    logger.debug("Writing %s" % len(data))
                    xzp.stdin.write(data)

                    if current:
                        # Reduce looping, wait a bit for more data
                        sleep(0.5)
            except(KeyboardInterrupt, SystemExit):
                raise
            finally:
                xzp.stdin.flush()
                xzp.stdin.close()

            position = fileStream.tell()

        inotifyx.rm_watch(fd, watcher)
    finally:
        os.close(fd)

    # Get return code
    xzp.wait()
    if xzp.returncode is not 0:
        logger.error("xz gave non-zero exit status")
        return None
    # logger.debug("xz return code: %s" % (returnCode))

    # Check new compressed file exists (before this we don't *actually* know
    # it does because it's a shell redirect)
    try:
        with open(outputFile):
            pass
    except IOError:
        logger.error("Failed to create xz file")
        return None

    return (outputFile, position)


def subprocessSetup():
    # Prevents SIGINT from getting sent to subprocesses. By default, Python
    # SIGINTs subprocesses when it has finished writing. Since we need to
    # keep xz's stdin open for multiple writes, we need to enforce the
    # system's default behaviour for SIGPIPE events by declaring SIG_DFL.

    # os.setpgrp()
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def handler(signum, frame):
    global gInputFile
    global gOutputFile

    # Signal handler function
    logger.info("Signal %s called" % signum)

    # Figure out the current file and clean it up
    raise SystemExit    # cleanup(gOutputFile)
    logger.info("Exiting")


def cleanup(outputFile):
    logger.warning("Cleaning up %s" % outputFile)

    # Truncate
    with io.open(outputFile, mode='w'):
        pass
    # Delete
    os.unlink(outputFile)


def run():
    # Globals for signal handlers (ugly - better way?)
    global gInputFile
    global gOutputFile

    # Define signal handler for exits
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGQUIT, handler)

    # List files
    files = listFiles(sourceDirectory, fileRegexes)
    # logger.debug("Found files:\n %s" % (str(files)))

    # Check there actually are files...
    if len(files) < 1:
        logger.error("No files found in %s, exiting" % sourceDirectory)
        # Nothing to cleanup() here
        raise SystemExit

    # Get first file and start
    inputFile = files[0]
    logger.debug("Starting with file %s" % inputFile)

    while 1:
        try:
            outputFile = inputFile + ".xz"

            gInputFile = inputFile
            gOutputFile = outputFile

            logger.info("Compressing %s to %s" % (inputFile, outputFile))

            # Compression block
            try:
                # xzCompress returns the resulting file name and the offset of
                # the file it read from
                xzResult, inputFileOffset = xzCompress(inputFile, outputFile)
            except IOError:
                logger.critical("IOError during compression of %s, perhaps xz "
                                "process terminated" % (inputFile))
                cleanup(outputFile)
                raise SystemExit
            except (KeyboardInterrupt, SystemExit):
                cleanup(outputFile)
                raise

            # Check the result
            if xzResult is not None:
                # Compression succeeded, make sure it is safe to truncate/
                # remove the file.
                newFile = nextFile(inputFile)
                logger.debug("Found new file, %s" % newFile)

                if newFile is None:
                    # Something has gone wrong here (maybe hitwriter crashed or
                    # this code sucks)
                    # Don't want to cleanup(outputFile) as it should be ok
                    logger.critical("Expected another file, bailing")
                    raise SystemExit
                    break

                logger.info("Compression succeeded, removing %s" % inputFile)
                try:
                    # os.unlink(inputFile)
                    os.rename(inputFile, inputFile + ".wouldBeDeleted")
                except:
                    logger.error("Could not remove %s, was it already deleted?"
                                 % inputFile)
                    raise SystemExit
            else:
                logger.critical("xz subprocess returned no compressed file "
                                "after compressing %s"
                                % inputFile)
                cleanup(outputFile)
                raise SystemExit
                break

        except (KeyboardInterrupt, SystemExit):
            # logger.info("Caught exit signal")
            break
        # oldFile = inputFile[:]
        inputFile = newFile

    sleep(0.1)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("sourceDirectory",
                        help='''The source directory (location of the log
                        files). This can be a directory with subdirectories
                        underneath. The script will recurse and process all
                        matching files beneath.''')
    parser.add_argument("-d", "--debug",
                        help="Enables debug output to console and log",
                        action="store_true")
    args = parser.parse_args()

    sourceDirectory = args.sourceDirectory

    # Setup logging
    if args.debug:
        logger = logSetup(logging.DEBUG)
        logger.info("Debug output enabled")
    else:
        logger = logSetup(logging.INFO)

    logger.info("Logzipper start")
    run()
    logger.info("Logzipper end")
