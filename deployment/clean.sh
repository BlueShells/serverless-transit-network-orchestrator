#!/bin/bash


echo $1

python3 remove_stack.py --profile $1 -n zzm
python3 remove_tgw.py --profile $1 -n zzm
python3 remove_s3.py --profile $1 -n zzm
python3 remove_vpc.py --profile $1 --force
