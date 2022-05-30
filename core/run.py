import sys
import glob
import os
import json
import argparse
import time
import random

# from ..agent_manager.palet_manager import PaletManager

sys.path.append("../area/")
sys.path.append("../agent/")
sys.path.append("../agent_manager/")
sys.path.append("../building")

sys.path.append("../agent/robotData/")
sys.path.append("../agent/robotData/taskData")


from building import Building

from palet_manager import PaletManager
from robot_manager import RobotManager
from elevator_manager import ElevatorManager

# from RobotElevatorServer import RobotElevatorServer


MESH = 0.5 #meter
DURATION = 0.1
TASK = 500

class Engine():
    master = None
    def __init__(self):
        self.loop= False
        Engine.master = self
        self.building = None
        self.areas = []
        self.managers = []
        self.tasks = None
        self.taskCount = None
        self.time = 0
        
    def addBuilding(self, b):
        self.building = b
    
    def addManager(self, m):
        self.managers.append(m)

    def stop(self):
        self.loop = False
    
    def run(self,DURATION, speed = 1):
        self.loop = True
        while self.loop:
            # print('time', self.time)
            for manager in self.managers:
                manager.step(DURATION)
            self.time = round(self.time+DURATION,2)
        print('finish!!')


# need to be singletone!
def doit(config, r_allocation, h_shift, batch, pa_size, Activate, outputFile):
    if Engine.master == None:
        e = Engine()
        building = Building(config, pa_size, batch)
        building.generate()
        
        p_manager = PaletManager(building)
        r_manager = RobotManager(building, h_shift)
        e_manager = ElevatorManager(building)
        
        #双方向のリンク
        r_manager.link_manager([p_manager, e_manager])
        e_manager.link_manager(p_manager)
        p_manager.link_manager(e_manager)
        
        p_manager.generate_palets(TASK)
        r_manager.generate_robots(r_allocation)
        e_manager.generate_elevators()
        
        e.addManager(p_manager)
        e.addManager(r_manager)
        e.addManager(e_manager)
        
        e.addBuilding(building)
        
        print('building and agents are generated!! \n')

    else:
        e = Engine.master
    
    if not e.loop: 
        e.run(DURATION = 0.1, speed= 1)
    del e, floorArea, elvArea, reServer, roboManager, elvManager

def allocate_robot_ramdomly(fl_n, rnum):
    aloc = [1]*fl_n
    rnum -= fl_n
    for r in range(rnum):
        i = random.randint(1,fl_n)
        aloc[i-1] += 1
    return aloc

def main(args):
    config = args.config
    equal = int(args.robo_equal_dist)
    r_allocation = args.roboallocation
    h_shift = bool(args.h_shift)
    if args.batch:
        batch = int(args.batch)
    else:
        batch = args.batch
    pa_size = (float(args.pa_size), float(args.pa_size))
    mode = args.mode
    
    fl_n = int(config.split('.')[0][-2:])
    
    if equal != 0:
        r_allocation = tuple([equal]*fl_n)
    else:
        rnum = fl_n * 2
        r_allocation = allocate_robot_ramdomly(fl_n, rnum)
        
    if mode == 'normal':
        Activate = False
    elif mode == 'efficient':
        Activate = True

    outputFile = '../record/2022-03-02/robot{}.json'.format(r_allocation)


    doit(config, r_allocation, h_shift, batch, pa_size, Activate, outputFile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    #Building configuration
    parser.add_argument("--config", help='config file name', default='large_warehouse03.json')
    parser.add_argument("--record", help='record file name', default=None)

    #parameter
    parser.add_argument("--robo_equal_dist", help='The number of robot', default=0)
    parser.add_argument("--roboallocation", help='The number of robot', default=(2,2,2))    #ロボットの数と階層ごとの配分(1F, 2F, ..)
    parser.add_argument("--pa_size", help='pool_area_size', default=5) #　なしの場合は0
    parser.add_argument("--h_shift", help='hierarchical_shift', default=False) #ロボットも階層移動するか
    parser.add_argument("--batch", help='batch size(number)', default=None) #荷物をどの程度まとめて送るか(体積)
    

    #parameter(基本さわらない)
    parser.add_argument("--pool_area_pos", help='', default=None)   #WIP
    parser.add_argument("-m", "--mode", help='System mode (normal/efficient)', default='normal') #基本ノーマル（動作が信頼できるから）
    parser.add_argument("--task", help='Task file', default=None) #基本は自動生成
    args = parser.parse_args()
    main(args)
