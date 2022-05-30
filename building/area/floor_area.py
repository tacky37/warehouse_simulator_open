import matplotlib.pyplot as plt
import random

from .base_area import BaseArea
from .pool_area import PoolArea
from .elv_wait_area import ElvWaitArea


class FloorArea(BaseArea):
    def __init__(self, id, pos, floor, mesh):
        super(FloorArea, self).__init__(name='floor_area' + str(floor), type='floor_area', id=id, pos=pos, floor=floor, mesh=mesh, prohibit=False)
        self.building = None
        self.child_areas = {}
        self.floor_area = self
        self.generate_countour(self.pos, self.mesh)
    
    def generate_countour(self, pos, mesh):
        x1, y1, x2, y2 = pos[0], pos[1], pos[3], pos[4]
        ox = []
        oy = []
        
        for x in [x1, x2]:
            y = y1
            while(y<=y2):
                ox.append(x)
                oy.append(y)
                y+=mesh

        for y in [y1, y2]:
            x = x1
            while(x<=x2):
                ox.append(x)
                oy.append(y)
                x+=mesh
        self.ox.extend(ox)
        self.oy.extend(oy)
    
    def link_area(self, areas):
        for area in areas:
            if area.type not in self.child_areas.keys():
                self.child_areas[area.type] = [area]
            else:
                self.child_areas[area.type].append(area)
            self.ox.extend(area.ox)
            self.oy.extend(area.oy)
            area.floor_area = self
            
    def link_building(self, building):
        self.building = building
            
    def ignite(self, pa):
        self.building.ignite(pa)
    
    def unignite(self, pa):
        self.building.unignite(pa)
    
    def sent_unavailable(self, area):
        self.building.sent_unavailable(area)
            
    def sent_available(self, area):
        self.building.sent_available(area)
    
    def sent_collect_batch_size_palet(self, area):
        self.building.sent_collect_batch_size_palet(area)
            
    def show(self):
        plt.plot(self.ox, self.oy, ".k", )
        plt.xlabel('[m]')
        plt.ylabel('[m]')
        plt.grid(True)
        plt.axis("equal")
        plt.savefig("floor{}.png".format(random.randint(0,99)))
        plt.show()
        pass
    
    def getStates(self):
        states = []
        for area in self.child_areas:
            states.append(area.getState())
        return states

############################ ↓外部クラスとの通信的やり取り ##################################

############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################