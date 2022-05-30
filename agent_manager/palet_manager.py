from re import A
import sys
import random

sys.path.append("../agent/")
sys.path.append("./")
sys.path.append("./util/")

from base_manager import BaseManager
from palet_agent import PaletAgent
from utils import find_closest_area
from output import output
class PaletManager(BaseManager):
    def __init__(self, building):
        super(PaletManager, self).__init__(name='palet_manager', type='palet_manager', building=building)
        self.Agent = PaletAgent
        self.tasks = {}                 #まだ目的地にたどり着いていない$ & ロボットに割り当てられていない
        '''
        1:{'s->p':[],'p->w':[], 'w->e':[],} 'pickup->pop'でタスクを登録, floorはpickupのフロア
        '''
        self.completed_task = []
        self.task_record = {}

    def generate_palets(self, num):
        size = (1.0, 1.0, 0.5)
        d_areas = {}

        for id in range(num):
            df = random.choice(self.building.floors)
            while True:
                destination_area = random.choice(df.child_areas['shelf_area'])
                if str(destination_area) not in d_areas.keys():
                    d_areas[str(destination_area)] = destination_area.capacity - size[0]*size[1]*size[2]
                    break
                elif d_areas[str(destination_area)] >= size[0]*size[1]*size[2]:
                    d_areas[str(destination_area)] -= size[0]*size[1]*size[2]
                    break
                else:
                    continue
                
            weight =round(random.uniform(5, 50), 1)
            deadline = None
            agent = self.Agent(id, None, None, size, weight, deadline, self)
            
            if df.floor == 1:
                cf = random.choice(self.building.floors[1:])
            else:
                cf = self.building.floors[0]
            
            while True:
                current_area = random.choice(cf.child_areas['shelf_area'])
                if agent.update_ground_area(current_area):
                    agent.set_pos(list(current_area.center))
                    agent.c_area = current_area             #良くない
                    agent.d_area = destination_area         #良くない
                    n_area = self.get_next_areas([agent])[0]#良くない
                    self.send_update_areas(agent, (current_area, n_area, destination_area))
                    # agent.n_area = self.get_next_areas([agent])[0]
                    break
                else:
                    pass
            
            if agent.c_area.floor not in self.tasks.keys():
                self.tasks[agent.c_area.floor] = {}
            self.append_task(agent)
            
            self.task_record[str(agent)] = {}
            self.task_record[str(agent)]["pickup"] = str(agent.c_area)
            self.task_record[str(agent)]["destination"] = str(agent.d_area)
            self.task_record[str(agent)]["size"] = agent.size
            self.task_record[str(agent)]["weight"] = agent.weight
            self.task_record[str(agent)]["deadline"] = agent.deadline
            self.task_record[str(agent)]["completed_time"] = None
            
            self.agents.append(agent)
    
    #'pickup->pop', next_areaの更新はpopのタイミングでのみ行われる
    def get_next_areas(self, agents):
        n_areas = []
        n_area = None
        for agent in agents:
            area = agent.c_area
            d_area = agent.d_area       #shelf_area
            #print(self, area, d_area)
            
            if area == None:
                n_area = agent.n_area # 更新しない
            
            if area == d_area:
                n_area = None
            elif area.floor == d_area.floor:
                if area.type == 'elv_area':
                    n_area, i = find_closest_area(agent.pos, area.floor_area.child_areas['pool_area'])
                elif area.type == 'pool_area':
                    n_area = d_area
                elif area.type == 'floor_area':
                    n_area = d_area
            else:
                if area.type == 'shelf_area':
                    n_area, i = find_closest_area(agent.pos, area.floor_area.child_areas['pool_area'])
                elif area.type == 'floor_area':
                    n_area = agent.n_area   #更新しない
                elif area.type == 'pool_area':
                    n_area, i = find_closest_area(agent.pos, area.floor_area.child_areas['elv_area'])
                elif area.type == 'wait_area':
                    n_area, i = find_closest_area(agent.pos, area.floor_area.child_areas['elv_area'])  
                elif area.type == 'elv_area':
                    n_area, i = find_closest_area(agent.pos, d_area.floor_area.child_areas['elv_area'])     #本当はフロア間でエレベータエリアを紐付けるべき
            n_areas.append(n_area)
        #print(self, n_areas)
        return n_areas
    
    def get_current_areas(self, agents):
        areas = []
        for agent in agents:
            areas.append(agent.c_area)
        return areas

    def update_task(self, palet):
        pass
    
    def append_task(self, palet):
        if palet.c_area == palet.d_area:
            print(self, self.time, '\033[42m'+'{} is completed'.format(palet)+'\033[0m')
            if len(self.completed_task) == len(self.task_record):
                print(self, self.time, '\033[42m'+'All of task is completed'.format(palet)+'\033[0m')
                sys.exit(0)
            self.completed_task.append(palet)
            return
        else:
            ca = palet.c_area.type[0]
            na = palet.n_area.type[0]
            key = ca+'->'+na
            if key not in self.tasks[palet.c_area.floor].keys():
                self.tasks[palet.c_area.floor][key] = []
            self.tasks[palet.c_area.floor][key].append(palet)
            print(self.time, self, key, palet, 'append')

    def remove_task(self, palet):
        ca = palet.c_area.type[0]
        na = palet.n_area.type[0]
        key = ca+'->'+na
        if palet in self.tasks[palet.c_area.floor][key]:
            self.tasks[palet.c_area.floor][key].remove(palet)
        else:
            pass
        print(self.time, self, key, palet, 'remove')
    
    def get_agents(self):
        return self.agents
    
    def step(self, duration):
        self.time = round(self.time+duration,2)
        

############################ ↓外部クラスとの通信的やり取り ##################################
    #別のフロアのelv_areaへのpop
    def rcv_elv_arrival(self, elv):
        for obj in elv.objs:
            if obj.type == 'palet_agent':
                self.remove_task(obj)
                c_area = elv.c_area
                obj.c_area = c_area   #良くない, get_next_areaがc_areaを利用する関係での実装
                n_area = self.get_next_areas([obj])[0]
                d_area =  obj.d_area
                self.send_update_areas(obj, (c_area, n_area, d_area))
                self.append_task(obj)
                
    #elv_areaからのpickup
    def rcv_elv_departure(self, elv):
        for obj in elv.objs:
            if obj.type == 'palet_agent':
                c_area = elv.c_area
                #obj.c_area = c_area   #良くない, get_next_areaがc_areaを利用する関係での実装
                n_area = obj.n_area
                # n_area = self.get_next_areas([obj])[0]
                d_area =  obj.d_area
                self.send_update_areas(obj, (c_area, n_area, d_area))

    #paletを載せているロボット・エレベータ(エレベータの到着と出発はpickup, popを伴う）の移動に伴ったエリア更新
    def rcv_update_palet_area(self, palet, area):
        c_area = area
        n_area = palet.n_area
        d_area =  palet.d_area
        self.send_update_areas(palet, (c_area, n_area, d_area))

    def rcv_pickup_palet(self, palet, area):
        c_area = area
        palet.c_area = area   #良くない, get_next_areaのがc_areaを利用する関係
        # n_area = self.get_next_areas([palet])[0]
        n_area = palet.n_area
        d_area =  palet.d_area
        self.send_update_areas(palet, (c_area, n_area, d_area))
    
    def rcv_pop_palet(self, palet, area):
        c_area = area
        palet.c_area = area   #良くない, get_next_areaのがc_areaを利用する関係
        n_area = self.get_next_areas([palet])[0]
        d_area =  palet.d_area
        self.send_update_areas(palet, (c_area, n_area, d_area))
        
        if palet.c_area == palet.d_area:
            self.completed_task.append(palet)
            self.task_record[str(palet)]["completed_time"] = self.time
            print(self, self.time, '\033[42m'+'{} is completed, remain task:{}'\
                .format(palet, len(self.task_record)-len(self.completed_task))+'\033[0m')
            # if len(self.task_record)-len(self.completed_task) < 5:
            #     self.task_record.keys() - self.completed_task
            for fl, fl_task in self.tasks.items():
                for cd, task in fl_task.items():
                    if task:
                        print(self, self.time, \
                            '\033[42m'+'remain task : {}'.format((fl, cd))+'\033[0m')
                        
            if len(self.completed_task) == len(self.task_record):
                print(self, self.time, '\033[42m'+'All of task is completed'.format(palet)+'\033[0m')
                output(self.building, self.time)
                sys.exit(0)
            
            return
        
        self.append_task(palet)
    
    def rcv_allocated_task(self, palet):
        print(self.time, self, palet, palet.g_area, palet.c_area, palet.n_area, palet.d_area, 'is allocated')
        self.remove_task(palet)
        
############################ ↑外部クラスとの通信的やり取り ##################################
