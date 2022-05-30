
from base_agent import BaseAgent
import numpy as np
import copy

#エレベータを表現するエージェント

#ロボットの状態
STANDBY, PICKUP, DELIVER, MOVE_TO_ELV, WAIT_ELV, GET_IN, IN_ELV, GET_OUT = 1, 2, 3, 4, 5, 6, 7, 8
#エレベータからのレスポンス
SUCESS, FAIL, OTHER, AUTO = 1, 2, 3, 99
#ロボットが向かいたい方向、状態
STOP, UP, DOWN, PAUSE = 'stop', 'up', 'down', 'pause'
#エレベータへの乗り込み情報（ロボットステータス）
BOARDED, GOT_OFF, CANCELL_BOARD, CANCELL_GET_OFF, OPEN_DOOR = 1, 2, 3, 4, 5
#ドアの情報
CLOSE, OPEN = 0, 1
#エレベータへの乗降時間
BOARDING_TIME = 10
#エレベータの自動扉閉時間
OPEN_LIMIT = 300


class ElevatorAgent(BaseAgent):
    def __init__(self, id, pos, c_area, size, weight, manager):
        super(ElevatorAgent, self).__init__(name='elevator'+str(id).zfill(4), type='elevator_agent', id=id, pos=pos,\
            c_area=c_area, size=size, weight=weight, manager=manager)
        self.m_speed = 3.0        #[m/s]
        self.w_capa = 100.0           #積載可能重量
        self.s_capa = size[0]*size[1]*(size[2]-1)   #空間キャパ
        self.space = self.s_capa
        self.objs = []
        
        self.door  = CLOSE
        self.state = STOP
        
        self.tmp_time = 0

        #output用
        self.travel_dist = 0
        self.move_time = 0
        print(self, self.s_capa, 'a'*30)
    
    # ↓twinuから引き継ぎ
        self.openButton = False
        self.direction = STOP
        self.upButton = np.zeros(len(self.c_area.room), dtype=np.int)
        self.downButton = np.zeros(len(self.c_area.room), dtype=np.int)
        self.stopButton = np.zeros(len(self.c_area.room), dtype=np.int)

        self.robotStatus =[]
        self.waitCount = 0
        self.robot = set()
        
        self.inRobot = []
        self.outRobot = []
        
    
    
    def findClosestFloor(self, current_area, button, dir):
        #floor = self.g_area.floor
        floor = current_area.floor
        #自フロアの検索
        if dir == 'both':
            if button[floor-1] != 0:
                return self.g_area.room[floor]
        #自フロアを中心に上下階の探索を行う
        for i in range(len(button)):
            i+=1
            #自フロアより上の検索
            if dir in ['both', 'up']:
                if floor+i <= len(button):
                    if button[floor+i-1]!= 0:
                        # print('closestFloor; F{}'.format(floor+i+1))
                        return self.g_area.room[floor+i]
            #自フロア未満の検索
            if dir in ['both', 'down']:
                #1階を見る
                if floor-i >= 1:
                    if button[floor-i-1]!= 0:
                        #print('closestFloor; F{}'.format(floor-i+1))
                        return self.g_area.room[floor-i]
        return None
    
    def stop(self, duration):
        button = self.upButton + self.downButton + self.stopButton
        if np.sum(button) == 0:
            return
        else:
            closest_fa = self.findClosestFloor(self.g_area, button, dir='both')
            #print(self.time, self, self.g_area, closest_fa)
            if self.g_area.floor> closest_fa.floor:
                self.state = DOWN
                self.direction = DOWN
                self.__send_elv_departure()
            elif self.g_area.floor< closest_fa.floor:
                self.state = UP
                self.direction = UP
                self.__send_elv_departure()
            else:
                if self.downButton[self.g_area.floor-1] == 1:
                    self.direction = DOWN
                    self.downButton[self.g_area.floor-1] =0
                    self.stopButton[self.g_area.floor-1] =0
                elif self.upButton[self.g_area.floor-1] == 1:
                    self.direction = UP
                    self.upButton[self.g_area.floor-1] =0
                    self.stopButton[self.g_area.floor-1] =0
                elif self.stopButton[self.g_area.floor-1] == 1:
                    self.direction = STOP
                    self.stopButton[self.g_area.floor-1] =0
                self.state = PAUSE
                self.door = OPEN
        print('{}   elv state; STOP -> {}'.format(self.time,self.state))
        print('{}   elv direction;{}, floor;{}, door;{}, elv upB;{}, downB;{}, stopB{}'.format(self.time, self.direction, self.g_area.floor, self.door, self.upButton, self.downButton, self.stopButton), self.pos)
                
    def up(self, duration):
        #ボタンの確認
        button = self.upButton + self.stopButton
        # 自分より上の一番近いフロア取得
        relay_area = self.findClosestFloor(self.g_area, button, dir='up')
        # 自分より上の一番遠いフロア取得
        if relay_area == None:
            button = button + self.downButton
            relay_area = self.findClosestFloor(self.g_area, button, dir='up')
        # 中継フロアがないときは次の階で停止
            if relay_area == None:
                relay_area = self.g_area.room[self.g_area.floor+1]

        self.pos[2] += + self.m_speed* duration
        self.travel_dist = round(self.travel_dist+self.m_speed*duration,4)
        # print(self.pos, self.g_area, relay_area, self.g_area.room, \
        #     self.g_area.room[len(self.g_area.room)].center[2], self.g_area.room[self.g_area.floor].center[2])
        # 最上階の高さを超えない
        if self.pos[2] > self.g_area.room[len(self.g_area.room)].center[2]:
            self.pos[2] = copy.deepcopy(self.g_area.room[len(self.g_area.room)].center[2])
        #自フロアのひとつ上のフロアの高さを上回る
        # print('aaaa',self.time, self, self.pos[2], self.g_area.room[self.g_area.floor+1],\
        #     self.g_area.room[self.g_area.floor+1].center, relay_area, relay_area.center, \
        #         self.g_area.room[len(self.g_area.room)], self.g_area.room[len(self.g_area.room)].center[2])
        if self.pos[2] >= self.g_area.room[self.g_area.floor+1].center[2]:
            #ひとつ上のフロアに更新
            self.__send_transit_floor(self.g_area.room[self.g_area.floor+1])
            self.update_ground_area(self.g_area.room[self.g_area.floor+1])
            self.update_objs_ground_area()
            self.pos[2] = copy.deepcopy(self.g_area.center[2])

        # エレベータ内部のロボットを動かす
        self.move_objs()
        if self.g_area != relay_area:
            return 

        button = self.downButton + self.stopButton + self.upButton
        # 自分より上のフロアのボタンが押されているか
        if np.sum(button[self.g_area.floor:]) >= 1:
            self.direction = UP     # そのまま
            self.upButton[self.g_area.floor-1] = 0
        else:
            if self.upButton[self.g_area.floor-1] == 1:
                self.direction = UP
                self.upButton[self.g_area.floor-1] = 0
            elif self.downButton[self.g_area.floor-1] == 1:
                self.direction = DOWN
                self.downButton[self.g_area.floor-1] = 0
            else:
                self.direction = STOP
        self.stopButton[self.g_area.floor-1] = 0
        print('{}   elv state; UP -> PAUSE'.format(self.time))
        print('{}   elv direction;{}, floor;{}, door;{}, elv upB;{}, downB;{}, stopB{}, robotstatus;{}'.format(self.time,self.direction, self.g_area.floor, self.door, self.upButton, self.downButton, self.stopButton, self.robotStatus), relay_area, self.pos)
        self.state = PAUSE
        #ひとつ上のフロアに更新
        # self.update_ground_area(self.g_area)
        # self.update_objs_ground_area()
        self._send_elv_arrival()
        self.door = OPEN
    
    def down(self, duration):
        #ボタンの確認
        button = self.downButton + self.stopButton
        # 自分未満の一番近いフロア取得
        relay_area = self.findClosestFloor(self.g_area, button, dir='down')
        # 自分未満の一番遠いフロア取得
        if relay_area == None:
            button = button + self.upButton
            relay_area = self.findClosestFloor(self.g_area, button, dir='down')
        # 中継フロアがないときは次の階で停止
            if relay_area == None:
                relay_area = self.g_area.room[self.g_area.floor-1]

        self.pos[2] -= self.m_speed* duration
        self.travel_dist = round(self.travel_dist+self.m_speed*duration,4)
        if self.pos[2] < self.g_area.room[1].center[2]:
            self.pos[2] = copy.deepcopy(self.g_area.room[1].center[2])
        
        #自フロアのひとつ下のフロアの高さを下回る
        # #print('bbbb',self.time, self, self.pos[2], self.g_area.room[self.g_area.floor-1],\
        #     self.g_area.room[self.g_area.floor-1].center, relay_area, relay_area.center, \
        #         self.g_area.room[len(self.g_area.room)], self.g_area.room[len(self.g_area.room)].center[2])
        if self.pos[2] <= self.g_area.room[self.g_area.floor-1].center[2]:
            self.__send_transit_floor(self.g_area.room[self.g_area.floor-1])
            self.update_ground_area(self.g_area.room[self.g_area.floor-1])
            self.update_objs_ground_area()
            self.pos[2] = copy.deepcopy(self.g_area.center[2])
        # エレベータ内部のロボットを動かす
        self.move_objs()
        
        if self.g_area != relay_area:
            return

        button = self.downButton + self.stopButton + self.upButton
        # 自分より下のフロアのボタンが押されているか
        if np.sum(button[:self.g_area.floor-1]) >= 1:
            self.direction = DOWN
            self.downButton[self.g_area.floor-1] = 0
        else:
            if self.downButton[self.g_area.floor-1] == 1:
                self.direction = DOWN
                self.downButton[self.g_area.floor-1] = 0
            elif self.upButton[self.g_area.floor-1] == 1:
                self.direction = UP
                self.upButton[self.g_area.floor-1] = 0
            else:
                self.direction = STOP
        self.stopButton[self.g_area.floor-1] = 0

        print('{}   elv state; DOWN -> PAUSE'.format(self.time))
        print('{}   elv direction;{}, floor;{}, door;{}, elv upB;{}, downB;{}, stopB{}, robotstatus;{}'.format(self.time, self.direction, self.g_area.floor, self.door, self.upButton, self.downButton, self.stopButton, self.robotStatus), relay_area, self.pos)
        self.state = PAUSE
        # self.update_ground_area(self.g_area)
        # self.update_objs_ground_area()
        self._send_elv_arrival()
        self.door = OPEN
    
    def pause(self, duration):
        # self.tmp_time = round(self.tmp_time+duration, 2)
        # if self.tmp_time > OPEN_LIMIT:
        #     self.door = CLOSE
        #     self.state = self.direction
        # print('{}   elv door;{},robotstatus;{}'.format(self.time, self.door, self.robotStatus))
        if self.openButton:
            self.waitCount = 0
            return
        else:
            self.waitCount = round(self.waitCount+duration,3)
            # print('{}   elv PAUSE waitCount:{}'.format(self.time, self.waitCount))

        if self.waitCount > BOARDING_TIME:
            self.door = CLOSE
            self.waitCount = 0
            self.openButton = False
            self.state = self.direction
            if self.state in [UP, DOWN]:
                self.__send_elv_departure()
        else:
            return
        print('{}   elv state; PAUSE -> {}'.format(self.time, self.state))
        print('{}   elv direction;{}, floor;{}, door;{}, elv upB;{}, downB;{}, stopB{}, robotstatus;{}'.format(self.time, self.direction, self.g_area.floor, self.door, self.upButton, self.downButton, self.stopButton, self.robotStatus), self.pos)

    def step(self,duration):
        # ロボットからの呼出しを受けていたら要求階に動き始める
        #print('elv state; {}, direction;{} z = {}, floor;{}, door;{}, robotstatus;{}'.format(self.state, self.direction, self.z, self.g_area.floor, self.door, self.robotStatus))
        self.time = round(self.time+duration,2)
        if self.state == STOP:
            self.stop(duration)
        elif self.state == UP:
            self.move_time = round(self.move_time+duration,2)
            self.up(duration)
        elif self.state == DOWN:
            self.move_time = round(self.move_time+duration,2)
            self.down(duration)
        elif self.state == PAUSE:
            self.pause(duration)

    def getState(self):
        return {
            'type':'elv',
            'id':self.id, 
            'state':self.state,
            'scount':self.time,
            'pos': list(self.pos)
        }

############################ ↓外部クラスとの通信的やり取り ##################################
    def __send_transit_floor(self, area):
        self.manager.rcv_transit_floor(self, area)

    def _send_elv_arrival(self):
        print(self.time, self, 'c_area', self.g_area, 'g_area', self.g_area, 'd_area', self.d_area, self.pos,'arrival')
        self.manager.rcv_elv_arrival(self)
        
    def __send_elv_departure(self):
        print(self.time, self, self.g_area,self.g_area, self.d_area, self.pos, 'departure')
        self.manager.rcv_elv_departure(self)
############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################
    def move_objs(self):
        for obj in self.objs:
            obj.change_height(self.pos[2])
    
    def update_objs_ground_area(self):
        for obj in self.objs:
            if obj.update_ground_area(self.g_area):
                pass

    def __transfer_to_other(self, durateion, obj, area):
        pass
    
    def transfer_from_other(self, duration, obj, area):
        pass
############################ ↑外部クラスとの物理的やり取り ##################################                

    def pushButton(self, msgs):
        for msg in msgs:
            dst = msg['origination']
            if (self.state == PAUSE) and (self.g_area.floor== dst) and (self.direction == STOP):
                self.direction = msg['direction']
                print('\033[32m'+'{}   direction:{}'.format(self.time, self.direction)+'\033[0m')
                return
            
            if msg['direction'] == STOP:
                self.stopButton[dst-1] = 1
            elif msg['direction'] == UP:
                self.upButton[dst-1] = 1
            elif msg['direction'] == DOWN:
                self.downButton[dst-1] = 1

    def resRegistration(self, msg):
        res = {
            'api'           : 'RegistrationResult',
            'result'        : SUCESS,     # 1:成功、2:失敗、3:その他エラー、99:管制運転中
            'elevator_id'   : 000000000,
            'timestamp'     : None
        }
        return res
    
    def res_call_elv(self, msg):
        self.pushButton([msg])
        #print('{}   elv upB;{}, downB;{}, stopB{}, '.format(self.time, self.upButton, self.downButton, self.stopButton))
        res = {
            'api'       : 'CallElevatorResult',
            'result'    : SUCESS,     # 1:成功、2:失敗、3:その他エラー、99:管制運転中
            'timestamp' : None
        }
        return res
    
    def resElvStatus(self, msg):
        res = {
            'api'           : 'ElevatorStatus',
            'result'        : SUCESS,
            'floor'         : self.g_area.floor,
            'door'          : self.door,            # 0:前後ドア閉状態、1:フロントドア完全開状態、2: リアドア完全開状態、3:前後ドア完全開状態
            'direction'     : self.direction,
            'timestamp'     : None
            }
        
        return res

    def res_robot_status(self, msg):
        self.openButton = False
        i = 0
        register = False
        for s in self.robotStatus:
            if s['robot_id'] == msg['robot_id']:
                self.robotStatus[i] = msg
                register = True
            else:
                pass
            i+=1
        if not register:
            self.robotStatus.append(msg)
        
        result = SUCESS
        if msg['state'] == BOARDED:
            self.openButton = False
            self.robot.add(msg['robot_id'])
            # print('{}   {}'.format(self.time, self.robot))
        elif msg['state'] == GOT_OFF:
            self.openButton = False
            i = 0
            for r in self.robot:
                if r == msg['robot_id']:
                    self.robot.discard(i)
                i += 1
            # print('{}   robot in elv: {}'.format(self.time, self.robot))
        elif msg['state'] == OPEN_DOOR:
            self.openButton = True
            if len(self.robot) >= self.s_capa and msg['robot_id'] not in self.robot:
                result = FAIL

        for s in self.robotStatus:
            if s['state'] == OPEN_DOOR:
                self.openButton = True

        res = {
            'api'           : 'RobotStatusResult',
            'result'        : result,
            'timestamp'     : None
        }
        # print(self.time, self, 'open button', str(self.openButton))
        return res
    
    def resReleaseResult(sefl, msg):
        res = {
            'api'           : 'RobotStatusResult',
            'result'        : SUCESS,
            'timestamp'     : None
        }
        return res
    
    def handleMsg(self, msg):
        api =msg['api']
        if api == 'Registration':
            res = self.resRegistration(msg)
        elif api == 'CallElevator':
            res = self.res_call_elv(msg)
        elif api == 'RequestElevatorStatus':
            res = self.resElvStatus(msg)
        elif api == 'RobotStatus':
            res =self.res_robot_status(msg)
        elif api == 'Release':
            res = self.resReleaseResult(msg)
            
        return res

    # def getInternalState(self):
    #     return {
    #         'type'          : 'elv',
    #         'id'            : self.id, 
    #         'name'          : self.name,
    #         'state'         : self.state,
    #         'scount'        :self.stateCount,
    #         'button'        : [self.upButton, self.downButton, self.stopButton],
    #         'pos': [self.x, self.y, self.z]
    #     }