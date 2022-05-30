import numpy as np


class BaseArea:
    def __init__(self, name, type, id, pos, floor, mesh, prohibit):
        self.name = name        #string
        self.type = type        #string(floor, pool, ...)
        self.id = id            #int
        self.pos = pos        #((x1,y1,z1, x2,y2,z2))
        
        self.floor = floor      #int(F1->1, F2->2)
        self.floor_area = None
        self.mesh = mesh        #float(default=50)
        self.prohibit = prohibit    #Bool
        self.ox = []
        self.oy = []
        self.ox, self.oy = self.generate_occupancy(self.pos, self.mesh, self.prohibit)
        self.center = self.calc_center_coordinate(self.pos)
        self.capacity = self.calc_capacity(self.pos)
        self.space = self.capacity
        self.objs = []
        self.ignite_flag = False
        self.full_flag = False
        print(self, self.pos, self.center)


    def __str__(self):
        return self.name
    
    # オキュパンシーグリッド作成（中身埋める）
    def generate_occupancy(self, pos, mesh, prohibit):
        x1, y1, x2, y2 = pos[0], pos[1], pos[3], pos[4]
        ox = []
        oy = []
        if prohibit:
            x, y = x1, y1
            while (x<=x2):
                while(y<=y2):
                    ox.append(x)
                    oy.append(y)
                    y+=mesh
                x+=mesh
                y = y1
        return ox, oy
    
    def calc_center_coordinate(self, pos):
        cx = (pos[0] + pos[3]) / 2
        cy = (pos[1] + pos[4]) / 2
        cz = (pos[2] + pos[5]) / 2
        center = (cx, cy, cz)
        return center
        
    def calc_capacity(self, pos):
        capa = (pos[3]-pos[0])*(pos[4]-pos[1])
        return capa
    
    def put_obj(self, obj):
        # print(self, obj, obj.size)
        s = self.space - obj.size[0]*obj.size[1]
        if s >= 0:
            self.space = s
            self.objs.append(obj)
            return True
        else:
            return False
        
    def rm_obj(self, obj):
        if obj in self.objs:
            self.objs.remove(obj)
            self.space += obj.size[0]*obj.size[1]
            return True
        else:
            return False

############################ ↓外部クラスとの通信的やり取り ##################################

############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################


    # def step(self,duration):
    #     for a in self.agents:
    #         a.step(duration)




