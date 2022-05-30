def generate_area( Area, id, poss, floor, mesh):
    areas = []

    for p in range(0, len(poss), 6):
        pos = []
        pos = poss[p:p+6]
        area = Area(id, pos, floor, mesh)
        areas.append(area)
        id+=1
    return areas