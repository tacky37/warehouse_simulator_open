from .base_area import BaseArea


class PoolArea(BaseArea):
    def __init__(self, id, pos, floor, mesh, batch):
        self.height = 1.5
        super(PoolArea, self).__init__(name='pool_area'+str(floor).zfill(2)+str(id).zfill(3), type='pool_area', id=id, pos=pos, floor=floor, mesh=mesh, prohibit=False)
        self.batch = batch
        self.set_delivery_loc()
    
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
        
    def set_delivery_loc(self):
        dx1 = self.center[0] + (self.pos[3] - self.pos[0])/2 + self.mesh*2
        dx2 = self.center[0] - (self.pos[3] - self.pos[0])/2 - self.mesh*2
        dy3 = self.center[1] + (self.pos[4] - self.pos[1])/2 + self.mesh*2
        dy4 = self.center[1] - (self.pos[4] - self.pos[1])/2 - self.mesh*2
        dloc1 = (dx1, self.center[1], self.center[2])
        dloc2 = (dx2, self.center[1], self.center[2])
        dloc3 = (self.center[0], dy3, self.center[2])
        dloc4 = (self.center[0], dy4, self.center[2])
        #棚の両脇が荷物の受渡位置
        # self.dlv_locs =  [dloc1, dloc2, dloc3, dloc4]
        self.dlv_locs =  [dloc1, dloc3, dloc4]
        # for dl in [dloc1, dloc3, dloc4]:
        #     print(dl[0])
        #     self.ox.append(dl[0])
        #     self.oy.append(dl[1])
    
    def calc_capacity(self, pos):
        capa = (pos[3]-pos[0])*(pos[4]-pos[1])*self.height
        return capa

    def getStates(self):
        states = []
        return states
    
############################ ↓外部クラスとの通信的やり取り ##################################
    def ignite(self):
        if self.ignite_flag == False:
            self.ignite_flag = True
            self.floor_area.ignite(self)
    
    def unignite(self):
        if self.ignite_flag:
            self.ignite_flag = False
            self.floor_area.unignite(self)
    
    def sent_unavailable(self):
        if not self.full_flag:
            self.full_flag = True
            self.floor_area.sent_unavailable(self)
            
    def sent_available(self):
        if self.full_flag:
            self.full_flag = False
            self.floor_area.sent_available(self)
    
    def sent_collect_batch_size_palet(self):
        self.floor_area.sent_collect_batch_size_palet(self)
############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################
    def put_obj(self, obj):
        s = self.space - obj.size[0]*obj.size[1]*obj.size[2]
        if s >= 0:
            self.space = s
            self.objs.append(obj)
            if self.space < self.capacity*0.2 and not self.ignite_flag:
                self.ignite()
            elif self.batch:
                if (self.capacity - self.space) >= self.batch:
                    self.sent_collect_batch_size_palet()
            print(self, self.space, 'rcv: ', obj)
            return True
        else:
            self.sent_unavailable()
            return False
        
    def rm_obj(self, obj):
        if obj in self.objs:
            self.objs.remove(obj)
            self.space += obj.size[0]*obj.size[1]*obj.size[2]
            if self.space > self.capacity*0.5 and self.ignite_flag:
                self.unignite()
            self.sent_available()
            print(self, self.space, 'rm: ', obj)
            return True
        else:
            return False
############################ ↑外部クラスとの物理的やり取り ##################################