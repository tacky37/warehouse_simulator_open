import asyncio
import sys
from tkinter import Pack
import numpy as np
import socketio
import glob
import json

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

MESH = 0.5 #meter
DURATION = 0.1
TASK = 500


class Engine():
    master = None
    def __init__(self,sio=None):
        self.sio = sio
        self.loop= False
        print("Engine",sio)
        Engine.master = self
        self.areas = []
        self.managers = []
        self.tasks = None
    
    def addBuilding(self, b):
        self.building = b
    
    def addManager(self, m):
        self.managers.append(m)

    def stop(self):
        self.loop = False

    async def run(self ,sio, DURATION, speed = 1):
        self.loop = True
        while self.loop:
            # print('time', self.time)
            for manager in self.managers:
                manager.step(DURATION)
            states = []
            for manager in self.managers:
                state = manager.getStates()  
                states.extend(state)
            await sio.emit('events',states)
            await asyncio.sleep(DURATION/speed)
            self.time = round(self.time+DURATION,2)

    async def run(self,sio,duration, speed = 1):
        self.loop = True
        while self.loop:
            for area in self.areas:
                area.step(duration)
            for manager in self.managers:
                manager.step(duration)
            states = []
            for manager in self.managers:
                state = manager.getStates()  
                states.extend(state)
            await sio.emit('events',states)
            await asyncio.sleep(duration/speed)
        print("Engine stopped")


# need to be singletone!
async def doit(sio, config='../config/large_warehouse03.json', r_allocation=(5,5,5), h_shift=False, batch=None, pa_size=(1, 1), Activate=False, outputFile='../record/2022-03-02/robot{}.json'.format(3)):
    if Engine.master == None:
        e = Engine(sio)
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
        await e.run(sio, duration = 0.1, speed= 1)

async def addPacket():
    if Engine.master != None:
        Engine.master.addPacket()

# async def addTruck():
#     if Engine.master != None:
#         Engine.master.addTruck()

# async def showRoads():
#     print("Show roadsEV, Engine.master={}".format(Engine.master))
#     if Engine.master != None:
#         await Engine.master.showRoads()


async def stop(sio):
    print("called from web!",sio)
    Engine.master.stop()
