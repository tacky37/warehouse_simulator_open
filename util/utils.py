import math

def find_closest_area(pos, areas):
    min_d = 10000000000000000
    c_area  = None
    index = 0
    c_index = None
    for area in areas:
        if not area:
            continue
        d = abs(math.dist(pos, area.center))
        if d < min_d:
            min_d = d
            c_area = area
            c_index = index
        index += 1
    return c_area, c_index

def find_closest_agent(pos, agents):
    min_d = 10000000000000000
    c_agent  = None
    index = 0
    for agent in agents:
        if not agent:
            continue
        d = abs(math.dist(pos, agent.pos))
        if d < min_d:
            min_d = d
            c_agent = agent
            c_index = index
        index += 1
    return c_agent, c_index

# def get_next_area_type(c_area, d_area):
#     n_areas = []
#     n_area = None

    
#     if c_area == d_area:
#         n_area = None
#         pass
#     elif c_area.floor == d_area.floor:
#         if c_area.type == 'elv_area':
#             n_area, i = find_closest_area(c_area.pos, c_area.floor_c_area.child_areas['pool_area'])
#         elif c_area.type == 'pool_area':
#             n_area = d_area.type
#         elif c_area.type == 'floor_area':
#             n_area = d_area.type
#     else:
#         if c_area.type == 'shelf_area':
#             n_area, i = find_closest_area(agent.pos, c_area.floor_c_area.child_areas['pool_area'])
#         elif c_area.type == 'floor_area':
#             n_area = None   #更新しない
#         elif c_area.type == 'pool_area':
#             n_area, i = find_closest_area(agent.pos, c_area.floor_c_area.child_areas['wait_area'])
#         elif c_area.type == 'wait_area':
#             n_area, i = find_closest_area(agent.pos, c_area.floor_c_area.child_areas['elv_area'])  
#         elif c_area.type == 'elv_area':
#             n_area, i = find_closest_area(agent.pos, d_area.floor_c_area.child_areas['elv_area'])     #本当はフロア間でエレベータエリアを紐付けるべき
#     n_areas.append(n_area)
#     #print(self, n_areas)
#     return n_areas
