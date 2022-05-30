import datetime
import json
import os
from urllib.error import ContentTooShortError

def output(building, comp_time, deadloc=False):
    content = {'input':{}, 'output':{}, 'task':{}, 'config':{}, 'info':{}}
    robot_manager = building.managers['robot_manager']
    palet_manager = building.managers['palet_manager']
    elv_manager = building.managers['elevator_manager']
    
    #task
    task_record = palet_manager.task_record
    content['task'] = task_record
    
    # 建物構成
    config = building.config
    # pa_pos = []
    for floor in building.floors:
        for pa in floor.child_areas['pool_area']:
            if 'pools' not in config['floor{}'.format(floor.floor)].keys():
                config['floor{}'.format(floor.floor)]['pools'] = [pa.pos]
            else:
                config['floor{}'.format(floor.floor)]['pools'].extend(pa.pos)
            # pa_pos.append(pa.pos)
    content['config'] = config
    
    # input
    robot_allocation = robot_manager.allocation
    pa_size = building.pa_size
    h_shift = str(robot_manager.h_shift)
    content['input']['robot_allocation'] = robot_allocation
    content['input']['pool_area_size'] = pa_size
    content['input']['batch'] = building.batch
    content['input']['hierarchical_shift'] = h_shift
    
    # robot info 
    #r_log = [['robot', 'size', 'max_speed', 'weight', 'capacity', 'floor', 'travel_distance', 'elevator_wait_time', 'move_time', 'action_time']]
    r_tr_dis = 0
    r_elv_w_time = 0
    r_move_time = 0
    r_action_time = 0
    r_log = {}
    for agent in robot_manager.agents:
        # log = [str(agent), agent.size, agent.m_speed, agent.weight, agent.w_capa, \
        #     agent.c_area.floor, agent.travel_dist, agent.elv_wait_time, agent.move_time, agent.action_time]
        #r_log.append(log)
        r_tr_dis += agent.travel_dist
        r_elv_w_time += agent.elv_wait_time
        r_move_time += agent.move_time
        r_action_time += agent.move_time
        r_log[str(agent)] = {}
        r_log[str(agent)]['size'] = agent.size
        r_log[str(agent)]['max_speed'] = agent.m_speed
        r_log[str(agent)]['weight'] = agent.weight
        r_log[str(agent)]['capacity'] = agent.s_capa
        r_log[str(agent)]['floor'] = agent.c_area.floor
        
        r_log[str(agent)]['travel_distance'] = agent.travel_dist
        r_log[str(agent)]['elevator_wait_time'] = agent.elv_wait_time
        r_log[str(agent)]['move_time'] = agent.move_time
        r_log[str(agent)]['action_time'] = agent.action_time
        r_log[str(agent)]['standby_time'] = agent.standby_time
        
    # elevator info
    #e_log = [['elevator', 'size', 'max_speed', 'weight', 'capacity', 'travel_distance', 'move_time']]
    e_log = {}
    for agent in elv_manager.agents:
        # log = [str(agent), agent.size, agent.m_speed, agent.weight, agent.w_capa, \
        #     agent.travel_dist, agent.move_time]
        # e_log.append(log)
        e_log[str(agent)] = {}
        e_log[str(agent)]['size'] = agent.size
        e_log[str(agent)]['max_speed'] = agent.m_speed
        e_log[str(agent)]['weight'] = agent.weight
        e_log[str(agent)]['capacity'] = agent.s_capa
        
        e_log[str(agent)]['travel_distance'] = agent.travel_dist
        e_log[str(agent)]['move_time'] = agent.move_time

    #output
    if not deadloc:
        content['output']['deadloc_time'] = 0
        content['output']['complete_time'] = comp_time
    if deadloc:
        content['output']['deadloc_time'] = comp_time
        content['output']['complete_time'] = 0
    # o_column = ['complete_time', 'robot_travel_distance', 'robot_elevator_wait_time' 'robot_wait_time', 'robot_move_time', 'robot_action_time', 'elevator_travel_distance', 'elevator_move_time']
    # o_content = 
    
    content['info'] = {'robot':r_log, 'elevator':e_log}
    
    #ファイルパス
    building_type = config['building_type']
    floor = 'floor' + str(len(building.floors)).zfill(2)
    robonum = 'robonum' + str(len(robot_manager.agents)).zfill(3)
    today = str(datetime.date.today())
    dt_now =  datetime.datetime.now()
    time = str(dt_now.hour) + '-' + str(dt_now.minute)
    now = today+'-'+time
    # proportion = ''
    # for fr in robot_allocation:
    #     proportion += str(fr)
    
    if h_shift == 'True' and sum(pa_size):
        hp = 'H_P/pool{}'.format(str(int(pa_size[0]*pa_size[1])).zfill(4))
    elif h_shift == 'True' and not sum(pa_size):
        hp = 'H'
    else:
        hp = 'P/pool{}'.format(str(int(pa_size[0]*pa_size[1])).zfill(4))

    record_path = '../record/{}/{}/{}/{}'.format(building_type, floor, robonum, hp)
    os.makedirs(name=record_path, exist_ok=True)
    f_name = '../record/{}/{}/{}/{}/{}.json'.format(building_type, floor, robonum, hp, now)
    #書き込み
    with open(f_name, mode='w') as f:
            json.dump(content, f)