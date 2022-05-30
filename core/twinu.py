#
## core file for Twinu: Ditital Twin Scalable Platform

import subprocess

def main():
    #start master clock
    masterCommand = ["python","../master_clock/master.py"]
    masterProc = subprocess.Popen(masterCommand)
    print("Start!", masterProc)

    #wait until
    masterProc.wait()

if __name__ == '__main__':
    main()