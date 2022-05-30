import sys

from .base_area import BaseArea


class ElvArea(BaseArea):
    def __init__(self, id, pos, floor, mesh):
        super(ElvArea, self).__init__(name='elv_area'+str(floor).zfill(2)+str(id).zfill(3), type='elv_area', id=id, pos=pos, floor=floor, mesh=mesh, prohibit=False)
        self.generate_countour(self.pos, self.mesh)
        self.dlv_locs = [self.center]
        self.room = {}
        self.room_name = None
        self.agent = None        
    
    def generate_countour(self, pos, mesh):
        x1, y1, x2, y2 = pos[0], pos[1], pos[3], pos[4]
        ox = []
        oy = []
        
        for x in [x1]:
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
        
    def set_room(self, rooms):
        for room_name, room in rooms.items():
            if room[self.floor] == self:
                self.room = room
                self.room_name = room_name
        # print(self, self.room_name, self.room)
    

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
            print(self, 'is unavailable')
            self.floor_area.sent_unavailable(self)
            
    def sent_available(self):
        if self.full_flag:
            self.full_flag = False
            self.floor_area.sent_available(self)
############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################
    #そのままエレベータエーゲントに横流し
    def put_obj(self, obj):
        print(self, self.floor, 'rcvd obj is ', obj, obj.type)
        if obj.type == 'elevator_agent':
            self.agent = obj
            print(self, 'space=', self.agent.space, self.agent.s_capa, self.center, self.pos, self.agent.g_area, self.agent.objs)
            if self.agent.space < self.agent.s_capa*0.2 and not self.ignite_flag:
                    self.ignite()
            if self.agent.space > 0:
                self.sent_available()
            return True
        elif self.agent == None:
            return False
        if obj in self.agent.objs:
            return True
        else:
            s = self.agent.space - obj.size[0]*obj.size[1]*obj.size[2]
            if s >= 0:
                self.agent.space = s
                self.agent.objs.append(obj)
                print(self, 'space=', self.agent.space, 'rcvd obj is ', obj, obj.type, self.agent.g_area, self.agent.objs)
                if self.agent.space < self.agent.s_capa*0.2 and not self.ignite_flag:
                    self.ignite()
                return True
            else:
                self.sent_unavailable()
                print(self, 'rejected obj is ', obj, obj.type)
                return False
            
    def rm_obj(self, obj):
        print(self, self.floor, 'rmvd obj is ', obj, obj.type)
        if obj.type == 'elevator_agent':
            self.agent = None
            self.unignite()
            self.sent_unavailable()
        else:
            if not self.agent:
                return True
            if obj in self.agent.objs:
                self.agent.objs.remove(obj)
                self.agent.space += obj.size[0]*obj.size[1]*obj.size[2]
                self.sent_available()
                print(self, 'space=', self.agent.space, 'rmbd obj is ', obj, obj.type, self.agent.g_area, self.objs)
                if self.agent.space > self.agent.s_capa*0.5 and self.ignite_flag:
                    self.unignite()
                return True
            else:
                return False

############################ ↑外部クラスとの物理的やり取り ##################################
