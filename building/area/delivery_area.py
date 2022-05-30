from .base_area import BaseArea


class DeliveryArea(BaseArea):
    def __init__(self, id, pos, floor, mesh):
        super(DeliveryArea, self).__init__(name='delivery_area'+str(floor).zfill(2)+str(id).zfill(3), type='delivery_area', id=id, pos=pos, floor=floor, mesh=mesh, prohibit=True)
        self.dlv_locs = None
        # self.set_delivery_loc()

    # def set_delivery_loc(self):
    #     dx1 = self.center[0] + (self.pos[3] - self.pos[0])/2 + self.mesh*2
    #     dx2 = self.center[0] - (self.pos[3] - self.pos[0])/2 - self.mesh*2
    #     dloc1 = (dx1, self.center[1], self.center[2])
    #     dloc2 = (dx2, self.center[1], self.center[2])
    #     #棚の両脇が荷物の受渡位置
    #     self.dlv_locs =  [dloc1, dloc2]
    
    def getStates(self):
        states = []
        return states

############################ ↓外部クラスとの通信的やり取り ##################################

############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################