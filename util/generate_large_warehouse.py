"""
floor{
    num:3
    size:(100, 40, 9) #(horizontal,vertical,height) 横,縦、高さ
}, 
area{
    shelfs{
        1F:[
            (x1, y1, x2, y2),
            ....
            ],
        2F:[
            ()..
        ]
        ...
    }, 
    
    elevator{
        (x1,y1,x2,y2),
        ..
    }
    
}
"""

import sys
import copy
import glob
import os
import json
import argparse

sys.path.append("../config/")

ORIGIN = [0, 0, 0]
SHELF = (2.0, 16.0)
MESH = 0.5
ELV = (2.0, 5.0)



def main(args):
    build_type = 'large_warehouse'

    floornum = int(args.floornumber)
    floorsize =args.floorsize
    path = '../config/{}{}'.format(build_type, str(floornum).zfill(2)) + '.json'
    content = {}
    
    
    content['building_type'] = build_type
    
    for fl in range(floornum):
        flname = 'floor{}'.format(fl+1)
        content[flname] = {}
        
        #各フロアの棚生成
        s_proportion = 0.2
        shelfs = []
        x = floorsize[0]*s_proportion
        y = 2.0
        z = fl*floorsize[2]
        while True:
            shelfs.extend([x,y,z,x+SHELF[0],y+SHELF[1],z]) #[x1,y1,z1,x2,y2,z2]
            x += SHELF[0] + 3.0
            if (x+SHELF[0]) > floorsize[0]*(1-s_proportion):
                x = floorsize[0]*s_proportion
                y += SHELF[1] + 3.0
            if (y+SHELF[1]) > floorsize[1]:
                break
        
        #各フロア生成
        origin = copy.copy(ORIGIN)
        fl_pos = list(floorsize)
        fl_pos[2] = z
        origin[2] = z
        origin.extend(fl_pos)
        
        
        
        content[flname]['self'] = origin
        content[flname]['shelfs'] = shelfs
        content[flname]['elevator'] = [ORIGIN[0],floorsize[1]/2-ELV[1]/2, z, ORIGIN[0]+ELV[0], floorsize[1]/2+ELV[1]/2, z] #[x1,y1,x2,y2]

    print(content)
    
    if os.path.exists(path):
        print('The specified file already exists')
    else:
        with open(path, 'w') as f:
            json.dump(content, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    #Building configuration
    parser.add_argument("--floornumber", help='The number of floor', default=3)
    parser.add_argument("--floorsize", help='The size of floor(x,y,z)', default=(100, 40, 9))

    #parameter(基本さわらない)
    parser.add_argument("--pool_area_pos", help='', default=None)   #WIP
    
    args = parser.parse_args()
    main(args)