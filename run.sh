#!/bin/bash

set -vx

{
    CUDA_VISIBLE_DEVICES="3" python -u run_main.py \
        --task_name='SetPre4DEE' \
        --use_bert=False \
        --start_epoch=1 \
        --num_train_epochs=100 \
        --train_batch_size=16 \
        --gradient_accumulation_steps=16 \
        --train_file_name='train.json' \
        --dev_file_name='dev.json' \
        --test_file_name='test.json' \
        --train_on_multi_events=True \
        --train_on_single_event=True
}
