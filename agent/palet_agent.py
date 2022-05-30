

from base_agent import BaseAgent


class PaletAgent(BaseAgent):
    def __init__(self, id, pos, c_area, size, weight, deadline, manager):
        super(PaletAgent, self).__init__(name='palet'+str(id).zfill(4), type='palet_agent', id=id, pos=pos, \
            c_area=c_area,size=size, weight=weight, manager=manager)
        self.deadline = deadline    # 実装したい

        self.visible = True

################# ↓外部クラスとの通信的やり取り ######################

################# ↑外部クラスとの通信的やり取り ######################

################# ↓外部クラスとの物理的やり取り ######################
    def change_height(self, height):
        self.pos[2] = height
################# ↑外部クラスとの物理的やり取り ######################

    def getState(self):
        pos = list(self.pos) + [0]
        content = {
            'type'      :'packet',
            'name'      : self.name, 
            'id'        : self.id,
            'pos'       : pos,
            'vis'       : self.visible,
            'size'      : self.size
        }
        return content
