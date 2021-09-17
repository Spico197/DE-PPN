#!/bin/bash

set -vx

{
    CUDA_VISIBLE_DEVICES="3" python -u run_main.py \
        --task_name='SetPre4DEE' \
        --start_epoch=1 \
        --train_batch_size=16 \
        --gradient_accumulation_steps=16
}
