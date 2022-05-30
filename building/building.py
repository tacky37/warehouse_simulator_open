from ctypes import util
from math import floor
import sys
import time
import copy
import glob
import os
import pathlib
import json
from xml.dom.pulldom import END_DOCUMENT

sys.path.append("./")
sys.path.append("../util/")

from area.floor_area import FloorArea
from area.shelf_area import ShelfArea
from area.elv_area import ElvArea
from area.elv_wait_area import ElvWaitArea
from area.pool_area import PoolArea


def read_json(fname):
    print(fname)
    if os.path.basename(fname) == fname:
        path = pathlib.Path(__file__).parent.parent.resolve()
        fname = os.path.join(path, 'config/' + fname)
    return json.load(open(fname,'r'))

def generate_area( Area, id, poss, floor, mesh, batch=None):
    areas = []

    for p in range(0, len(poss), 6):
        pos = []
        pos = poss[p:p+6]
        if Area==PoolArea:
            area = Area(id, pos, floor, mesh, batch)
        else:
            area = Area(id, pos, floor, mesh)
        areas.append(area)
        id+=1
    return areas


class Building():
    def __init__(self, config, pa_size, batch):
        self.load_config(config)
        # self.config = self.read_json(config)
        self.pa_size = pa_size
        self.batch = batch
        self.pos = None
        self.mesh = 0.5
        self.floors = []
        self.elv_rooms = {}
        self.managers = {}
        
    def generate(self, vis=False):
        id = 0
        tmp_elv_areas = []
        
        for fl in range(len(self.config.keys())-1):
            # エレベータ待機エリアの位置設定（本当はエレベータの数が増えても大丈夫なようにしたい)
            ew_pos  = copy.copy(self.config['floor{}'.format(fl+1)]['elevator']) 
            ew_pos[0] = ew_pos[3]
            ew_pos[3] = ew_pos[3] + 3
            #プールエリアの位置設定（位置は固定、サイズが可変）（本当は複数対応したい）
            p_pos = copy.copy(self.config['floor{}'.format(fl+1)]['elevator']) 
            p_pos[0], p_pos[1] = p_pos[3] + 1, p_pos[4]
            p_pos[3], p_pos[4] = p_pos[0]+self.pa_size[0], p_pos[1]+self.pa_size[1]
            print('pool area pos', p_pos)

            #エリア生成
            f_area = generate_area(FloorArea, id, self.config['floor{}'.format(fl+1)]['self'], fl+1, self.mesh)[0]
            s_areas = generate_area(ShelfArea, 0, self.config['floor{}'.format(fl+1)]['shelfs'], fl+1, self.mesh)
            e_areas = generate_area(ElvArea, 0, self.config['floor{}'.format(fl+1)]['elevator'], fl+1, self.mesh)
            ew_areas = generate_area(ElvWaitArea, 0, ew_pos, fl+1, self.mesh)
            pa_areas = generate_area(PoolArea, 0, p_pos, fl+1, self.mesh, self.batch)
            
            
            f_area.link_area(s_areas)
            f_area.link_area(e_areas)
            f_area.link_area(ew_areas)
            f_area.link_area(pa_areas)
            f_area.link_building(self)
            
            self.floors.append(f_area)
            tmp_elv_areas.extend(e_areas)
            if vis:
                f_area.show()
            id += 1
        
        self.generate_elv_rooms(tmp_elv_areas)
        
            
    def add_manager(self, manager):
        self.managers[str(manager)] = manager
        
    def ignite(self, area):
        self.managers['robot_manager'].rcv_ignite(area)
    
    def unignite(self, area):
        self.managers['robot_manager'].rcv_unignite(area)
    
    def sent_unavailable(self, area):
        self.managers['robot_manager'].rcv_unavailable(area)
            
    def sent_available(self, area):
        self.managers['robot_manager'].rcv_available(area)
    
    def sent_collect_batch_size_palet(self, area):
        # pass
        self.managers['elevator_manager'].rcv_call_elv(area)
        
    def load_config(self, fname):
        print(fname)
        if os.path.basename(fname) == fname:
            path = pathlib.Path(__file__).parent.parent.resolve()
            fname = os.path.join(path, 'config/' + fname)
        self.config =  json.load(open(fname,'r'))

    def generate_area(self, Area, id, poss, floor, mesh, batch=None):
        areas = []

        for p in range(0, len(poss), 6):
            pos = []
            pos = poss[p:p+6]
            if batch:
                area = Area(id, pos, floor, mesh, batch)
            else:
                area = Area(id, pos, floor, mesh)
            areas.append(area)
            id+=1
        return areas
    
    def generate_elv_rooms(self, e_areas):
        e_dict = {}
        shapes = []
        id = 0
        for e_area in e_areas:
            shape = [e_area.pos[0], e_area.pos[1], e_area.pos[3], e_area.pos[4]]
            if shape not in shapes:
                shapes.append(shape)
                room_name = 'room' + str(id).zfill(2)
                e_dict[room_name] = {}
                e_dict[room_name][e_area.floor] =e_area
                id += 1
            else:
                index = shapes.index(shape)
                room_name = 'room' + str(index).zfill(2)
                e_dict[room_name][e_area.floor] = e_area
        
        for e_area in e_areas:
            e_area.set_room(e_dict)

        self.elv_rooms = e_dict
        print(self.elv_rooms)
            
    def getStates(self):
        states = []
        for f in self.floors:
            states.append(f.getState())
        return states


############################ ↓外部クラスとの通信的やり取り ##################################
    def res_get_area_by_type(self, type):
        pass
############################ ↑外部クラスとの通信的やり取り ##################################

############################ ↓外部クラスとの物理的やり取り ##################################

############################ ↑外部クラスとの物理的やり取り ##################################