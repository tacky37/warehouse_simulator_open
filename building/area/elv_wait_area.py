from .base_area import BaseArea


class ElvWaitArea(BaseArea):
    def __init__(self, id, pos, floor, mesh):
        super(ElvWaitArea, self).__init__(name='wait_area'+str(floor).zfill(2)+str(id).zfill(3), type='wait_area', id=id, pos=pos, floor=floor, mesh=mesh, prohibit=False)
        self.dlv_locs = [self.center]
    
    #     self.generate_countour(self.pos, self.mesh)
    
    # def generate_countour(self, pos, mesh):
    #     x1, y1, x2, y2 = pos[0], pos[1], pos[3], pos[4]
    #     ox = []
    #     oy = []
        
    #     for x in [x1, x2]:
    #         y = y1
    #         while(y<=y2):
    #             ox.append(x)
    #             oy.append(y)
    #             y+=mesh

    #     for y in [y1, y2]:
    #         x = x1
    #         while(x<=x2):
    #             ox.append(x)
    #             oy.append(y)
    #             x+=mesh
    #     self.ox.extend(ox)
    #     self.oy.extend(oy)
    
    
    def getStates(self):
        states = []
        return states
    
############################ ↓外部クラスとの通信的やり取り ##################################

############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################