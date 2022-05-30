from gettext import find
import sys
import random
import copy

sys.path.append("../agent/")
sys.path.append("./")
sys.path.append("../util/")

from base_manager import BaseManager
from elevator_agent import ElevatorAgent
from utils import find_closest_area, find_closest_agent

#ロボットが向かいたい方向、状態
STOP, UP, DOWN, PAUSE = 'stop', 'up', 'down', 'pause'

class ElevatorManager(BaseManager):
    def __init__(self, building):
        super(ElevatorManager, self).__init__(name='elevator_manager', type='elevator_manager', building=building)
        self.Agent = ElevatorAgent
        self.hold_elv = set()
        self.hold_elv_by_robot = set()
        self.tmp_time = 0

    def generate_elevators(self):
        weight = 500    #適当
        fl = 1          #初期フロア
        elv_areas = self.building.floors[fl-1].child_areas["elv_area"]
        
        id = 0
        for ea in elv_areas:
            init_pos =  list(copy.deepcopy(ea.center))
            size = ((abs(ea.pos[3]-ea.pos[0])-ea.mesh), abs(ea.pos[1]-ea.pos[4])-ea.mesh*2, 2.5)
            agent = self.Agent(id, init_pos, ea, size, weight, self)
            if not agent.update_ground_area(ea):
                    print("Error!! {} initialization".format(agent))
            self.send_update_areas(agent, (ea, None, None))
            agent._send_elv_arrival()
            self.agents.append(agent)
            id += 1
            


    def step(self,duration):
        self.time = round(self.time+duration,2)
        for a in self.agents:
            a.step(duration)
        # 荷物の目的フロアとエレベータの現在フロアが一致するときはエレベータホールド,よくない
        for a in self.agents:
            i = 0
            task = {}
            for obj in a.objs:
                if obj.d_area.floor not in task.keys():
                    task[obj.d_area.floor] = [obj]
                else:
                    task[obj.d_area.floor].append(obj)
                # if obj.d_area.floor == a.c_area.floor:
                #task.append((str(obj), str(obj.c_area), str(obj.n_area), str(obj.d_area), str(a.c_area)))
            if a.c_area.floor in task.keys():
                # print(self.time, self, 'hold',  a, 'tasks:', task)
                self.hold_elv.add(a)
                self.tmp_time = 0
            elif a.c_area.floor not in task.keys():
                self.tmp_time = round(self.tmp_time+duration,2)
                # print(self.time, self, 'release',  a)
                self.hold_elv.discard(a)
                msg = {
                    'api'           : 'RobotStatus',
                    'elevator_id'   : None,
                    'robot_id'      : 9999,
                    'state'         : 2,     # 1:乗り込み完了、2:降車完了、3:乗り込み中止、4:降車中止、5:ドア開継続要求
                    'timestamp'     : None
                }
                res = a.res_robot_status(msg)
                max_num = 0
                d_floor = None
                for floor, objs in task.items():
                    if len(objs) > max_num:
                        max_num = len(objs)
                        d_floor = floor
                if d_floor and (a.c_area.ignite_flag or self.tmp_time>180):
                    self.tmp_time = 0
                    direction = STOP
                    origin = d_floor
                    dst = d_floor
                    msg = {
                        'api'           : 'CallElevator',
                        'elevator_id'   : 000,
                        'origination'   : origin,
                        'destination'   : dst,
                        'direction'     : direction,
                        'timestamp'     : 000
                    }
                    res = self.agents[0].res_call_elv(msg)

        if self.hold_elv or self.hold_elv_by_robot and not a.c_area.ignite_flag:
            for elv in self.hold_elv:
                msg = {
                        'api'           : 'RobotStatus',
                        'elevator_id'   : None,
                        'robot_id'      : 9999,
                        'state'         : 5,     # 1:乗り込み完了、2:降車完了、3:乗り込み中止、4:降車中止、5:ドア開継続要求
                        'timestamp'     : None
                    }
                res = elv.res_robot_status(msg)
            for elv in self.hold_elv_by_robot:
                msg = {
                        'api'           : 'RobotStatus',
                        'elevator_id'   : None,
                        'robot_id'      : 9999,
                        'state'         : 5,     # 1:乗り込み完了、2:降車完了、3:乗り込み中止、4:降車中止、5:ドア開継続要求
                        'timestamp'     : None
                    }
                res = elv.res_robot_status(msg)


############################ ↓外部クラスとの通信的やり取り ##################################
    # def __send_update_palet_area(self, palet, area):
    #         self.managers['palet_manager'].rcv_update_palet_area(palet, area)
            
    # def __send_update_robot_area(self, robot, area):
    #         self.managers['robot_manager'].rcv_update_robot_area(robot, area)
    
    def __send_elv_aarival(self, elv):
        self.managers['robot_manager'].rcv_elv_arrival(elv)
        self.managers['palet_manager'].rcv_elv_arrival(elv)
    
    def __send_elv_departure(self, elv):
        self.managers['robot_manager'].rcv_elv_arrival(elv)
        self.managers['palet_manager'].rcv_elv_arrival(elv)

    def rcv_call_elv(self, w_area):
        e_areas = w_area.floor_area.child_areas['elv_area']
        e_area,i = find_closest_area(w_area.center, e_areas)
        
        direction = STOP
        origin = e_area.floor
        dst = e_area.floor
        msg = {
            'api'           : 'CallElevator',
            'elevator_id'   : 000,
            'origination'   : origin,
            'destination'   : dst,
            'direction'     : direction,
            'timestamp'     : 000
        }
        res = self.agents[0].res_call_elv(msg)
    
    def res_hold_elv(self, area):
        for agent in self.agents:
            if agent.c_area.floor == area.floor:
                msg = {
                    'api'           : 'RobotStatus',
                    'elevator_id'   : None,
                    'robot_id'      : self.id,
                    'state'         : 5,     # 1:乗り込み完了、2:降車完了、3:乗り込み中止、4:降車中止、5:ドア開継続要求
                    'timestamp'     : None
                }
                res = self.agents[0].res_robot_status(msg)
                self.hold_elv_by_robot.add(agent)
                return True
        return False
    
    def rcv_release_elv(self, area):
        for agent in self.agents:
            if agent.c_area == area:
                msg = {
                    'api'           : 'RobotStatus',
                    'elevator_id'   : None,
                    'robot_id'      : 9999,
                    'state'         : 2,     # 1:乗り込み完了、2:降車完了、3:乗り込み中止、4:降車中止、5:ドア開継続要求
                    'timestamp'     : None
                }
                res = self.agents[0].res_robot_status(msg)
                self.hold_elv_by_robot.discard(agent)
    
    def rcv_transit_floor(self, elv, area):
        c_area = area
        n_area = None
        d_area = elv.d_area
        self.send_update_areas(elv, (c_area, n_area, d_area))
        
    def rcv_elv_arrival(self, elv):
        c_area = elv.g_area
        n_area = None
        d_area = elv.d_area
        self.send_update_areas(elv, (c_area, n_area, d_area))
        self.__send_elv_aarival(elv)
    
    def rcv_elv_departure(self, elv):
        # if elv.direction == DOWN:
        #     n_area = elv.g_area.room[elv.g_area.floor-1]
        # elif elv.direction == UP:
        #     n_area = elv.g_area.room[elv.g_area.floor+1]
        # else:
        #     print('ERROR: no direction', self.time, self)
        c_area = elv.g_area
        n_area = None
        d_area = elv.d_area
        self.send_update_areas(elv, (c_area, n_area, d_area))
        self.__send_elv_departure(elv)

############################ ↑外部クラスとの通信的やり取り ##################################