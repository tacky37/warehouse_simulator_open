#!/bin/bash

# pool = (1 1.5 2 2.5 3 3.5 4 4.5 5 5.5 6 6.5 7 7.5 8 8.5)
# smallPool=(1 2 3 4 5 6 7 8 9 10)
smallPool=(1)
pHeight=1.5
pIgnite=0.8
#largePool=(1 2 3 4 5 6 7 8 9 10)
roboNum=(2)
batch=(1 3 5 7 9 11 13 15 17 19)
#building=("small_warehouse02.json" "small_warehouse03.json" "small_warehouse04.json" "small_warehouse05.json" "small_warehouse06.json" "small_warehouse07.json" "small_warehouse08.json" "small_warehouse09.json")
building=("small_warehouse_e3003.json" "small_warehouse_e3006.json" "small_warehouse_e3009.json")
#building=("small_warehouse03.json" "small_warehouse09.json")
# loopNum=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
loopNum=(1 2 3 4 5 6 7 8 9 10)

for buid in ${building[@]}; do
    for robo in ${roboNum[@]}; do
        for pool in ${smallPool[@]}; do
            for n in ${loopNum[@]}; do
                python run.py --config $buid --pa_size $pool --robo_equal_dist $robo
            done
        done
    done
done

# for n in ${loopNum[@]}; do
#     for buid in ${building[@]}; do
#         for robo in ${roboNum[@]}; do
#             for pool in ${smallPool[@]}; do
#                 for b in ${batch[@]}; do
#                     var=$(($pool * $pool * 2))
#                     if [ $b -gt $var ]; then
#                         continue
#                     else
#                         python run.py --config $buid --pa_size $pool --robo_equal_dist $robo --batch $b
#                     fi
#                 done
#             done
#         done
#     done
# done