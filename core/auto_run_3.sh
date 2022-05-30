#!/bin/bash

# pool = (1 1.5 2 2.5 3 3.5 4 4.5 5 5.5 6 6.5 7 7.5 8 8.5)
# largePool=(1 2 3 4 5 6 7 8 9 10)
largePool=(10 9 8 7 6 5 4 3 2 1)
pHeight=1.5
pIgnite=0.8
#largePool=(1 2 3 4 5 6 7 8 9 10)
roboNum=(3)
batch=(1 3 5 7 9 11 13 15 17 19)
#building=("large_warehouse02.json" "large_warehouse03.json" "large_warehouse04.json" "large_warehouse05.json" "large_warehouse06.json" "large_warehouse07.json" "large_warehouse08.json" "large_warehouse09.json")
building=("large_warehouse03.json" "large_warehouse06.json" "large_warehouse09.json")
#building=("large_warehouse03.json" "large_warehouse09.json")
# loopNum=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
# loopNum=(1 2 3 4 5 6 7 8 9 10)
loopNum=(1 2 3 4 5)
for n in ${loopNum[@]}; do
    for buid in ${building[@]}; do
        for robo in ${roboNum[@]}; do
            for pool in ${largePool[@]}; do
                python run.py --config $buid --pa_size $pool --robo_equal_dist $robo
            done
        done
    done
done

# for n in ${loopNum[@]}; do
#     for buid in ${building[@]}; do
#         for robo in ${roboNum[@]}; do
#             for pool in ${largePool[@]}; do
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