from .base_area import BaseArea


class ShelfArea(BaseArea):
    def __init__(self, id, pos, floor, mesh):
        self.height = 2
        super(ShelfArea, self).__init__(name='shelf_area'+str(floor).zfill(2)+str(id).zfill(3), type='shelf_area', id=id, pos=pos, floor=floor, mesh=mesh, prohibit=True)
        self.dlv_locs = None
        self.set_delivery_loc()
    
    def calc_capacity(self, pos):
        capa = (pos[3]-pos[0])*(pos[4]-pos[1])*self.height
        return capa

    def set_delivery_loc(self):
        dx1 = self.center[0] + (self.pos[3] - self.pos[0])/2 + self.mesh*2
        dx2 = self.center[0] - (self.pos[3] - self.pos[0])/2 - self.mesh*2
        dloc1 = (dx1, self.center[1], self.center[2])
        dloc2 = (dx2, self.center[1], self.center[2])
        #棚の両脇が荷物の受渡位置
        self.dlv_locs =  [dloc1, dloc2]
        
    def put_obj(self, obj):
        # print(self, obj, obj.size)
        s = self.space - obj.size[0]*obj.size[1]*obj.size[2]
        if s >= 0:
            self.space = s
            self.objs.append(obj)
            return True
        else:
            return False
        
    def rm_obj(self, obj):
        if obj in self.objs:
            self.objs.remove(obj)
            self.space += obj.size[0]*obj.size[1]*obj.size[2]
            return True
        else:
            return False
    
    def getStates(self):
        states = []
        return states
    
############################ ↓外部クラスとの通信的やり取り ##################################

############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################