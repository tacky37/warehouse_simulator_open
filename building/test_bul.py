import sys
import glob
import os
import json
import argparse
import time


from building import Building

def main():
    # if os.path.basename(fname) == fname:
    #     path = pathlib.Path(__file__).parent.resolve()
    #     fname = os.path.join(path, fname)
    # config = json.load(open('../config/building5.json','r'))
    pa_size = (1, 1)
    buiding = Building('small_warehouse03.json', pa_size, None)
    buiding.generate(vis=True)

main()