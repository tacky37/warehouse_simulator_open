import copy
class BaseAgent:
    def __init__(self, name, type, id, pos, c_area, size, weight, manager):
        self.name = name        #string
        self.type = type        #string(floor, pool, ...)
        self.id = id            #int
        self.pos = pos          #((x1,y1,z1), center position
        self.size = size        # (横,縦,高さ
        self.weight = weight
        self.manager = manager
        self.c_area = c_area
        self.n_area = None
        self.d_area = None
        self.g_area = None      #接地エリア,物理的(パレットがロボットに乗っているときは接地エリアがない状態),
        #↑ g_area:エージェントのオキュパンシーグリッドの代替
        self.time = 0

    def __str__(self):
        return self.name

############################ ↓外部クラスとの通信的やり取り ##################################
    def rcv_update_areas(self, areas):
        self.c_area, self.n_area, self.d_area = areas

############################ ↑外部クラスとの通信的やり取り ##################################


############################ ↓外部クラスとの物理的やり取り ##################################
    def set_pos(self, pos):
        self.pos = list(copy.deepcopy(pos))

    #物理的にそのエリアに侵入できるかどうか判定して更新
    def update_ground_area(self,  area):
        if area:
            if not area.put_obj(self):
                return False
        if self.g_area:
            self.g_area.rm_obj(self)
        self.g_area = area
        return True
    # -> self.__send_arrival

############################ ↑外部クラスとの物理的やり取り ##################################
