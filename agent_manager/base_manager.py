
class BaseManager:
    def __init__(self, name, type, building):
        self.name = name        #string
        self.type = type        #string(floor, pool, ...)
        self.building = building
        self.Agent = None     #各エージェントクラス
        self.agents = []
        self.managers = {}
        self.time = 0
        
        self.link_building()

    def __str__(self):
        return self.name
    
    def link_building(self):
        self.building.add_manager(self)
    
    def link_manager(self, manager):
        self.managers[str(manager)] = manager
        print(self, manager, 'is linked')
    
    def step(self,duration):
        for a in self.agents:
            a.step(duration)

    def getStates(self):
        states = []
        for a in self.agents:
            states.append(a.getState())
        return states


############################ ↓外部クラスとの通信的やり取り ##################################
    def send_update_areas(self, agent, areas):
        agent.rcv_update_areas(areas)
############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################