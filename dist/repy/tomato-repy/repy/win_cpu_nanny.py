""" 
Author: Justin Cappos

Start Date: July 4th, 2008

Description:
Is the nanny for cpu on Windows.
"""
import time
import sys
import tracebackrepy
import nonportable
import windows_api as windows_api

def main():
  if len(sys.argv) != 4:
    print "Error, didn't get the right number of args:",sys.argv
    sys.exit(1)

  ppid = int(sys.argv[1])
  limit = float(sys.argv[2])
  freq = float(sys.argv[3])

  # run forever, checking the process' CPU use and stopping when appropriate
  try:
    while True:
    # Base amount of sleeping on return value of win_check_cpu_use to prevent under/over sleeping
      slept = nonportable.win_check_cpu_use(limit, ppid)

      if slept == -1:
        # Something went wrong, try again
        pass
      elif slept == 0:
        time.sleep(freq)
      elif (slept < freq):
        time.sleep(freq-slept)
    
      # see if the process exited...
      status = windows_api.process_exit_code(ppid)
      # Amazing! They rely on the programmer to not return 259 to know when 
      # something actually exited.   Luckily, I do control the return codes...
      if status != 259:
        sys.exit(0)

  except SystemExit:
    pass

  except windows_api.DeadProcess:
    # This can be caused when getting process times for a dead thread or
    # Trying to timeout a dead thread, either way, we just exit
    sys.exit(0)

  except:
    tracebackrepy.handle_exception()
    print >> sys.stderr, "Win nanny died!   Trying to kill everything else"
    
    # kill the program we're monitoring
    # Use newer api to kill process
    windows_api.kill_process(ppid)

if __name__ == '__main__':
  main()
