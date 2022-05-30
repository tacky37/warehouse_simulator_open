from re import A
import sys
from math import dist
import random
from xml.dom.pulldom import IGNORABLE_WHITESPACE

from sklearn.semi_supervised import SelfTrainingClassifier

sys.path.append("../agent/")
sys.path.append("./")
sys.path.append("../util/")

from base_manager import BaseManager
from robot_agent import RobotAgent
from utils import find_closest_area, find_closest_agent
from output import output

PICKUP, POP, WAIT = 'pickup', 'pop', 'wait'


class RobotManager(BaseManager):
    def __init__(self, building, h_shift):
        super(RobotManager, self).__init__(name='robot_manager', type='robot_manager', building=building)
        self.Agent = RobotAgent
        self.managers = {}
        self.h_shift = h_shift
        self.allocation = None
        self.ignite_areas = []
        self.unavailable_areas = set()
        self.available_pool_areas = set()
        self.valid_elvs = []
        self.call_floor = {}
        for fa in self.building.floors:
            self.call_floor[fa.floor] = False
        
        self.wait_robots = []
        self.standby_robots = []
        self.elv_robots = set()
        
        self.sync_time = 0
        self.deadloc_time = 0

        
    # num = (1,2,1) -> 1階に一台、2階に2台、3階に1台
    def generate_robots(self, allocation):
        size = (0.5, 1.0, 1.5)  #(横、縦、高さ)
        weight = 20.0           #与えるだけで使わない
        fl = 1
        id = 0
        n_entry_area = ['elv_area', 'shelf_area', 'pool_area']   #パレットだけ階層移動
        #n_entry_area = ['elv_area', 'shelf_area', 'pool_area']  #ロボットも階層移動
        self.allocation = allocation
        for num in allocation:
            f_area = self.building.floors[fl-1]
            init_pos = [3, 3, f_area.center[2]]            # 本当はフロアの障害物がないスペースにランダム生成する/ロボット待機エリアを生成する
            for n in range(num):
                agent = self.Agent(id, init_pos, f_area, size, weight, self, n_entry_area)
                if not agent.update_ground_area(f_area):
                    print("Error!! {} initialization".format(agent))
                self.send_update_areas(agent, (f_area, None, None))
                self.__send_floor(agent, f_area)
                #self.agents[str(agent)] = (f_area, None, None)  #(current area, next relay area, destination area), ロボットからの接地エリアをもとに決定
                self.agents.append(agent)
                self.standby_robots.append(agent)
                id += 1
            fl += 1
    
    def link_manager(self, managers):
        for manager in managers:
            self.managers[str(manager)] = manager
            print(self, manager, 'is linked')
            manager.link_manager(self)
    
    def manage_elv(self, robot):
        pass
    
    def get_prioritized_task(self, robot, ignite_areas, valid_elvs, skip_task):
        ig_p_areas = []
        ig_e_areas = []
        elv_areas = []
        # ロボットフロアでのpoolエリアの発火判定
        for ar in ignite_areas:
            if ar.floor == robot.c_area.floor:
                if ar.type == 'pool_area':
                    ig_p_areas.append(ar)
                elif ar.type == 'elv_area':
                    ig_e_areas.append(ar)
        for elv in valid_elvs:
            if elv.c_area.floor == robot.c_area.floor:
                elv_areas.append(elv.c_area)
                
        #p:pool, w:wait, s:shelf, 
        if ig_p_areas:
            if ig_e_areas:
                pr_tasks = {0:['e->p'], 1:['p->s'], 2:['s->p'], 3:['p->e']}
            elif elv_areas:
                pr_tasks = {0:['p->e'], 1:['p->s'], 2:['e->p']}
            else:
                #pr_tasks = {0:['p->s'], 1:['p->e']}
                pr_tasks = {0:['p->s']}
        else:
            if ig_e_areas:
                pr_tasks = {0:['e->p'], 1:['p->s', 's->p'], 2:['p->e']}
            elif elv_areas:
                pr_tasks = {0:['e->p'], 1:['p->e'], 2:['p->s', 's->p']}
            else:
                # pr_tasks = {0:['p->s', 's->p'], 1:['p->e']}
                pr_tasks = {0:['p->s', 's->p']}
        
        return pr_tasks

    def allocate_task(self, agent, actions, pr_tasks, ig_p_areas, valid_elvs):
        # ↑ 複数のig_area, elv_areaがあるときに上記情報を使わないと困る
        '''
        input: ↑
        output: (target palet, action, destination area)
        '''
        candidates = []
        c_agent1 = None
        #agentフロアの優先度の高いタスクを順に見る
        for task in pr_tasks.values():
            for t in task:
                if t in self.managers['palet_manager'].tasks[agent.c_area.floor].keys():
                    # print(self.time, self, agent, 'pass', t)
                    if PICKUP in actions:
                        pick_tasks = self.managers['palet_manager'].tasks[agent.c_area.floor][t]
                        pick_areas = self.managers['palet_manager'].get_current_areas(pick_tasks)
                        c_area1, c_index1 = find_closest_area(agent.pos, pick_areas)
                        if c_index1 is not None:
                            c_agent1 = pick_tasks[c_index1]
                            cand = (c_agent1, PICKUP, c_area1)
                            candidates.append(cand)
                
                if POP in actions:
                    for palet in agent.palets:
                        action, area = POP, palet.n_area
                        if palet.n_area.type[0] != t[-1]:
                            continue
                            ####↓ここおかしい，別フロアのタスク
                        #目的フロアでpool_areaが使えないときは直接棚，エレベータに持っていく
                        if area in self.unavailable_areas:
                            if palet.c_area.floor == palet.d_area.floor:
                                area = palet.d_area
                            elif area.type == 'pool_area' and actions==[POP]:
                                eas = self.building.floors[agent.c_area.floor-1].child_areas['elv_area']
                                area, i = find_closest_area(agent.pos, eas)
                        if area.type[0] == 'e':
                            palet, action, area = self.__navi_to_elv(agent, palet)
                        if area in self.unavailable_areas:
                            continue
                        cand = (palet, action, area)
                        candidates.append(cand)
            if not candidates:
                continue
            d_areas = []
            for cand in candidates:
                d_areas.append(cand[2])
            t_palet, index = find_closest_area(agent.pos, d_areas)
            value = candidates[index]
            if value[1] == PICKUP:
                self.__send_allocated_task(value[0])
            print(self.time, self, agent, pr_tasks, value)
            return value
        if pr_tasks in [{0:['p->s', 's->p']}, {0:['p->s']}]:
            if self.call_floor[agent.c_area.floor] is False:
                #↓急に高速化できた
                if self.managers['palet_manager'].tasks[agent.c_area.floor]['p->e'] or agent.palets:
                    self.__send_call_elv(agent.c_area)
                    pas = self.building.floors[agent.c_area.floor-1].child_areas['pool_area']
                    pa, i = find_closest_area(agent.pos, pas)
                    return (None, None, pa)
        return (None, None, None)
    
    #エレベータへの誘導
    def __navi_to_elv(self, agent, palet):
        for ve in self.valid_elvs:
            if ve.c_area.floor == agent.c_area.floor:
                return (palet, POP, palet.n_area)
        w_area, i = find_closest_area(\
            agent.pos, self.building.floors[agent.c_area.floor-1].child_areas['wait_area'])
        return (palet, None, w_area)

    def __navi_to_pool(self, agent, palet):
        pass
        
    def navi_with_elv(self, agent):
        if not agent.palets:
            actions = [PICKUP]
        # ロボットはpaletを持っていて、容量に空きがある
        elif agent.space > 0:
            actions = [PICKUP, POP]
        # ロボットの容量に空きがない
        else:
            actions = [POP]
            
        pr_tasks = self.get_prioritized_task(agent, self.ignite_areas, self.valid_elvs, None)

        val = self.allocate_task(agent, actions, pr_tasks, self.ignite_areas, self.valid_elvs)
        # print(self.time, self, agent, 'pr_task:', pr_tasks, val)
        return val
    
    def navi_with_pa(self, agent):
        # ロボットがpaletを一つも持っていない
        if not agent.palets:
            actions = [PICKUP]
        # ロボットはpaletを持っていて、容量に空きがある
        elif agent.space > 0:
            actions = [PICKUP, POP]
        # ロボットの容量に空きがない
        else:
            actions = [POP]
            
        pr_tasks = self.get_prioritized_task(agent, self.ignite_areas, self.valid_elvs, None)

        val = self.allocate_task(agent, actions, pr_tasks, self.ignite_areas, self.valid_elvs)
        # print(self.time, self, agent, 'pr_task:', pr_tasks, val)
        return val
    
    def navi_with_elv_pa(self, agent):
        print('Set pool area with h_shift is not supported\n')
        sys.exit(1)
    
    def navigate(self, agent):
        pa_space = self.building.pa_size[0] * self.building.pa_size[1]
        
        if pa_space < self.building.mesh and self.h_shift:
            t_palet, action, d_area = self.navi_with_elv(agent)
        elif pa_space >= self.building.mesh and not self.h_shift:
            t_palet, action, d_area = self.navi_with_pa(agent)
        elif pa_space < self.building.mesh and not self.h_shift:
            t_palet, action, d_area = self.navi_with_pa(agent)
        else :
            t_palet, action, d_area = self.navi_with_elv_pa(agent)
        
        return t_palet, action, d_area

############################ ↓外部クラスとの通信的やり取り ##################################
    def __send_navigation(self, robot):
        if robot in self.standby_robots:
            task = self.navigate(robot)
            if task == (None, None, None):
                return
            robot.rcv_navigation(task)
            self.standby_robots.remove(robot)
        if robot in self.wait_robots:
            task = self.navigate(robot)
            if task == (None, None, None):
                return
            robot.rcv_navigation(task)
            self.wait_robots.remove(robot)
    
    def __send_reset_task(self, robot):
        robot.rcv_reset_task()

    def __send_floor(self, robot, f_area):
        robot.rcv_floor(f_area)
    
    def __send_update_palet_area(self, palet, area):
        self.managers['palet_manager'].rcv_update_palet_area(palet, area)
        
    def __send_allocated_task(self, palet):
        self.managers['palet_manager'].rcv_allocated_task(palet)

    def __send_call_elv(self, w_area):
        if self.call_floor[w_area.floor] is False:
            self.managers['elevator_manager'].rcv_call_elv(w_area)
            print(self.time, self, '\033[32m'+'call elevator to floor{}'.format(w_area.floor)+'\033[0m')
            self.call_floor[w_area.floor] = True
        else:
            pass

    def __send_release_elv(self, robot, area):
        pass
        e_areas = area.floor_area['elevator_area']
        e_area, i = find_closest_area(robot.pos, e_areas)
        self.managers['elevator_manager'].rcv_release_elv(e_area)
    
    def __req_hold_elv(self, robot, area):
        pass
        msg = self.managers['elevator_manager'].res_hold_elv(area)
        if msg == True:
            pass
        else:
            self.__send_reset_task(robot)

    def rcv_elv_arrival(self, elv):
        self.call_floor[elv.c_area.floor] = False
        self.valid_elvs.append(elv)
        for w_robot in self.wait_robots:
            self.__send_navigation(w_robot)
        for obj in elv.objs:
            if obj.type == 'robot_agent':
                c_area = elv.c_area
                n_area = obj.n_area
                d_area = obj.d_area
                self.send_update_areas(obj, (c_area, n_area, d_area))
                for palet in obj.palets:
                    self.__send_update_palet_area(palet, obj.c_area)
    
    def rcv_elv_departure(self, elv):
        self.valid_elvs.remove(elv)
        for obj in elv.objs:
            if obj.type == 'robot_agent':
                c_area = elv.c_area
                n_area = obj.n_area
                d_area = obj.d_area
                self.send_update_areas(obj, (c_area, n_area, d_area))
                for palet in obj.palets:
                    self.__send_update_palet_area(palet, obj.c_area)

    #from elevator_manager
    def rcv_update_robot_area(self, robot, area):
        c_area = area
        n_area = robot.n_area
        d_area = robot.d_area
        self.send_update_areas(robot, (c_area, n_area, d_area))
        for palet in robot.palets:
            self.__send_update_palet_area(palet, area)
    
    def rcv_standby_robot(self, robot):
        if robot.c_area.type == 'wait_area':
            self.wait_robots.append(robot)
            for elv in self.valid_elvs:
                if elv.c_area.floor == robot.c_area.floor:
                    self.__send_navigation(robot)
                    return
            self.__send_call_elv(robot.c_area)
        else:
            self.standby_robots.append(robot)
    
    def rcv_pickup_palet(self, robot, palet, ):
        self.deadloc_time = 0
        self.managers['palet_manager'].rcv_pickup_palet(palet, robot.c_area)
    
    def rcv_pop_palet(self, robot, palet):
        self.deadloc_time = 0
        self.managers['palet_manager'].rcv_pop_palet(palet, robot.d_area)
        if robot.d_area.type == 'elvevator_area':
            pass
    
    def rcv_robot_departure(self, robot):
        c_area = robot.g_area
        n_area = robot.d_area
        d_area = robot.d_area
        self.send_update_areas(robot, (c_area, n_area, d_area))
        for palet in robot.palets:
            self.__send_update_palet_area(palet, robot.c_area)
        if n_area.type == 'elevator_area':
            self.elv_robots.add(robot)
            self.__req_hold_elv(robot, d_area)
        elif robot in self.elv_robots:
                self.elv_robots.discard(robot)
                i = 0
                for er in self.elv_robots:
                    if er.c_area.floor == robot.c_area.floor:
                        i+=1
                if i == 0:
                    self.__send_release_elv(robot, c_area)
            
    def rcv_robot_arrival(self, robot):
        c_area = robot.g_area
        n_area = robot.d_area
        d_area = robot.d_area
        #print(self.time, self, robot, 'arive at ', c_area)
        self.send_update_areas(robot, (c_area, n_area, d_area))
        for palet in robot.palets:
            self.__send_update_palet_area(palet, robot.c_area)

    def rcv_action_error(self, area, palet, action):
        # if action == POP:
        #     self.skip_pop_areas.add(area)
        pass
    
    def rcv_move_error(self, robot):
        pass
    
    def rcv_ignite(self, area):
        # if area.floor not in self.ignite_areas.keys():
        #     self.ignite_areas[area.floor] = [area]
        #     return
        # self.ignite_areas[area.floor].append(area)
        print(self.time, self, '\033[31m'+'ignite area: {}'.format(area)+'\033[0m')
        self.ignite_areas.append(area)
        self.__send_call_elv(area)
    
    def rcv_unignite(self, area):
        # self.ignite_areas[area.floor].remove(area)
        print(self.time, self, '\033[31m'+'unignite area: {}'.format(area)+'\033[0m')
        self.ignite_areas.remove(area)
        
    def rcv_unavailable(self, area):
        print(self.time, self, '\033[31m'+'unavailable area: {}'.format(area)+'\033[0m')
        self.unavailable_areas.add(area)
            
    def rcv_available(self, area):
        print(self.time, self, '\033[31m'+'available area: {}'.format(area)+'\033[0m')
        self.unavailable_areas.discard(area)

############################ ↑外部クラスとの通信的やり取り ##################################

    def operation(self, duration):
        if self.standby_robots:
            for robot in self.standby_robots:
                self.__send_navigation(robot)
        # if self.wait_robots:
        #     for robot in self.standby_robots:
        #         self.__send_navigation(robot)

    def step(self,duration):
        self.time = round(self.time+duration,2)
        self.sync_time  = round(self.sync_time+duration,2)
        self.deadloc_time  = round(self.deadloc_time+duration,2)
        
        self.operation(duration)
        for a in self.agents:
            a.step(duration)
        
        if self.deadloc_time > 3600:
            output(self.building, self.time-self.deadloc_time, True)
            print('DeadLoc!! No action from robot is detected!!')
            sys.exit(1)
        
        # if self.sync_time > 0.1:
        #     self.operation(duration)
        #     self.sync_time = 0
