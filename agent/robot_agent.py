from base_agent import BaseAgent
import math
import numpy as np
import random
import sys

sys.path.append('../util/')

from astar import AStarPlanner


# フロア
F1, F2, F3 = 0, 1, 2
#ロボットの状態
STANDBY, PICKUP, DELIVER, MOVE_TO_ELV, WAIT_ELV, GET_IN, IN_ELV, GET_OFF = 1, 2, 3, 4, 5, 6, 7, 8
MOVE, ACT = 9, 10
#エレベータからのレスポンス
SUCCESS, FAIL, OTHER, AUTO = 1, 2, 3, 99
#ロボットが向かいたい方向
STOP, UP, DOWN = 'stop', 'up', 'down'
#エレベータへの乗り込み情報
BOARDED, GOT_OFF, CANCELL_BOARD, CANCELL_GET_OFF, OPEN_DOOR = 1, 2, 3, 4, 5
#エレベータへの乗降時間
BOARDING_TIME = 3
# エレベータドア
CLOSE, OPEN = 0, 1
#1階層の高さ
FLOORHEIGHT = 9
#1階層の移動に要する時間
TRANSFER_TIME = FLOORHEIGHT/(1.5)   # FLOORHEIGHT / (duration*elvSpeed)
# エレベータ位置
ELV_LOC = None
# エレベータ待ちエリア
WAIT_ELV_AREA = [35, 18]
# エレベータエリア
ELV_AREA = [41, 18]
#X, Y, Z
X, Y, Z = 0, 1, 2

PICKUP, POP, WAIT = 'pickup', 'pop', 'wait'


class RobotAgent(BaseAgent):
    def __init__(self, id, pos, c_area, size, weight, manager, n_entry_area):
        self.a_star = None
        super(RobotAgent, self).__init__(name='robot'+str(id).zfill(4), type='robot_agent', id=id, pos=pos,\
            c_area=c_area, size=size, weight=weight, manager=manager)
        self.action = None
        self.m_speed = 1.5        #[m/s])
        self.w_capa = 100.0           #積載可能重量
        self.s_capa = (size[0]+0.5)*size[1]*size[2]
        self.path = None
        self.angle = 0
        
        self.palets = []
        self.space  = self.s_capa
        
        self.task_state = STANDBY

        self.calc = False
        
        self.n_entry_area = n_entry_area
        
        self.time = 0             #活動時間
        self.tmp_time = 0           #荷物を積み込む時間とか
        
        ## output用
        self.travel_dist = 0
        self.elv_wait_time = 0
        self.standby_time = 0
        self.move_time = 0
        self.action_time = 0
        
    
    def __calc_path(self, dlocs):
        sx, sy = self.pos[0], self.pos[1]
        min_d = 10000000
        for dloc in dlocs:
            if math.dist(self.pos, dloc) < min_d:
                min_d = math.dist(self.pos, dloc)
                d_pos = dloc
        # print(self.time, self, 'dpos', d_pos)
        dx, dy = d_pos[0], d_pos[1]
        rx, ry = self.a_star.planning(dx, dy, sx, sy)
        self.path = [rx, ry]
    
    def reset_navigation(self):
        self.d_area = None
        self.path = None
        self.action = None

############################ ↓外部クラスとの通信的やり取り ##################################
    def __send_pickup_palet(self, palet):
        self.manager.rcv_pickup_palet(self, palet)
        pass
    
    def __send_pop_palet(self, palet):
        self.manager.rcv_pop_palet(self, palet)
        pass
    
    def __send_standby_robot(self):
        #print(self.time, self, 'is standby in', self.c_area)
        self.manager.rcv_standby_robot(self)
    
    def __send_robot_departure(self):
        self.manager.rcv_robot_departure(self)
    
    def __send_robot_arrival(self):
        self.manager.rcv_robot_arrival(self)
    
    def __send_action_error(self, palet):
        
        self.manager.rcv_action_error(self.d_area, palet, self.action)
        pass
    
    def __send_move_error(self):
        self.manager.rcv_move_error(self)
    
    def rcv_navigation(self, navigation):
        self.t_palet, self.action, self.d_area = navigation
        if self.action:
            print(self.time, self, 'current:', self.c_area, 'rcved task: ', self.t_palet, self.action, self.d_area, 'do next')
    
    def rcv_reset_task(self):
        self.task_state = STANDBY
        self.reset_navigation()
    
    def rcv_floor(self, f_area):
        if f_area.type == 'floor_area':
            fa = f_area
        else:
            fa = f_area.floor_area
        self.a_star = AStarPlanner(fa.ox, fa.oy, fa.mesh, np.sqrt(self.size[:2])[0])
        
############################ ↑外部クラスとの通信的やり取り ##################################


############################ ↓外部クラスとの物理的やり取り ##################################
    #エレベータエージェントから呼び出される
    def change_height(self, height):
        self.pos[2] = height
        self.__change_palets_height(height)
    
    def __change_palets_height(self, height):
        for palet in self.palets:
            palet.change_height(height)

    #本当は担当エリアの荷物を載せられるだけ積むようにしたい
    def __pickup(self, duration, obj, area):
        self.tmp_time = round(self.tmp_time+duration,2)
        if self.tmp_time < obj.weight/5:
            return
        if obj.update_ground_area(None):
            obj.set_pos(self.pos)
            self.palets.append(obj)
            self.space -= obj.size[0]*obj.size[1]*obj.size[2]
            self.tmp_time = 0
            self.__send_pickup_palet(self.t_palet)
            print(self.time, self, self.action, obj, 'from', self.d_area, 'did')
            self.task_state = STANDBY
            self.reset_navigation()
            self.__send_standby_robot()
        else:
            print(self.time, self, 'cannot pickup', obj, self.space)
            self.__send_action_error(obj)
            self.task_state = STANDBY
            self.reset_navigation()
            self.__send_standby_robot()

    def __pop(self, duration, obj, d_area):
        self.tmp_time = round(self.tmp_time+duration,2)
        if self.tmp_time < obj.weight/6:
            return
        if obj.update_ground_area(d_area):
            obj.set_pos(d_area.center)
            self.palets.remove(obj)
            self.space += obj.size[0]*obj.size[1]*obj.size[2]
            self.tmp_time = 0
            self.__send_pop_palet(self.t_palet)
            print(self.time, self, self.action, obj, 'to', d_area, 'did')
            self.task_state = STANDBY
            self.reset_navigation()
            self.__send_standby_robot()
        else:
            print(self.time, self, 'cannot pop', obj, self.space)
            self.__send_action_error(obj)
            self.task_state = STANDBY
            self.reset_navigation()
            self.__send_standby_robot()
    
    def __transfer_to_other(self, durateion, obj, area):
        pass
    
    def transfer_from_other(self, duration, obj, area):
        pass
############################ ↑外部クラスとの物理的やり取り ##################################

    def __act(self, duration):
        if self.action == 'pickup':
            self.action_time = round(self.action_time+duration,2)
            self.__pickup(duration, self.t_palet, self.g_area)
        elif self.action == 'pop':
            self.action_time = round(self.action_time+duration,2)
            self.__pop(duration, self.t_palet, self.d_area)
        elif self.action == None:
            self.task_state = STANDBY
            self.reset_navigation()
            self.__send_standby_robot()
    
    def __move(self, duration):
        if self.calc:
            self.tmp_time = round(self.tmp_time+duration,2)
            if self.tmp_time > self.calc_time:
                self.__calc_path(self.d_area.dlv_locs)
                self.update_ground_area(self.g_area.floor_area)
                self.__send_robot_departure()
                self.tmp_time = 0
                self.calc = False
            else: 
                return

        if self.path[0]:
            self.move_time = round(self.move_time+duration,2)
            relay = [self.path[0][0], self.path[1][0], self.pos[2]]
            dif_x = relay[0] - self.pos[0]
            dif_y = relay[1] - self.pos[1]
            
            self.angle = math.atan2(dif_y, dif_x)
            self.pos[X] += duration*self.m_speed*math.cos(self.angle)
            self.pos[Y] += duration*self.m_speed*math.sin(self.angle)
            for palet in self.palets:
                palet.set_pos(self.pos)
            
            dist = abs(math.dist(relay, self.pos))
            if dist > self.m_speed*duration:
                return
            self.travel_dist = round(self.travel_dist+math.sqrt(dif_x**2+dif_y**2),4)
            self.pos = relay
            self.path[0].pop(0)
            self.path[1].pop(0)
            # print(self.time, self, self.pos)
        else:
            if self.d_area.type not in self.n_entry_area:
                if not self.update_ground_area(self.d_area):
                    self.tmp_time = round(self.tmp_time+duration,2)
                    if self.tmp_time > 10.0:
                        self.__send_move_error()
                        self.tmp_time = 0

            self.__send_robot_arrival()
            self.task_state = ACT
    
    def __standby(self, duration):
        if self.calc is False:
            if self.d_area:
                if self.d_area != self.g_area:
                    # print(self.time, self, self.action, self.t_palet, self.d_area, 'do next')
                    self.calc = True
                    self.calc_time =math.dist(self.pos, self.d_area.center) / 50  #経路計算時間のシミュレーション
                    self.task_state = MOVE
        if self.g_area.type == 'wait_area':
            self.elv_wait_time = round(self.elv_wait_time+duration,2)
        else:
            self.standby_time = round(self.standby_time+duration,2)
            

    def step(self, duration):  # devide position using duration
        self.time = round(self.time+duration,2)
        # print(self.time, self, self.pos)
        
        if self.task_state == STANDBY:
            self.__standby(duration)
        elif self.task_state == MOVE:
            self.__move(duration)
        elif self.task_state == ACT:
            self.__act(duration)

    def getState(self):
        pos  = list(self.pos) + [self.angle]
        return {
            'type': 'robot',
            'name': self.name,
            'task_state': self.task_state,
            'id': self.id,
            'pos': pos
        }
