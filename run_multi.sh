#!/bin/bash

set -vx

CUDA="2,3"
NUM_GPUS=2

{
    CUDA_VISIBLE_DEVICES=${CUDA} bash train_multi.sh ${NUM_GPUS} \
        --task_name='SetPre4DEE_1214_with_component_metrics' \
        --use_bert=False \
        --start_epoch=1 \
        --num_train_epochs=100 \
        --train_batch_size=16 \
        --gradient_accumulation_steps=4 \
        --learning_rate=0.00001 \
        --decoder_lr=0.00002 \
        --train_file_name='train.json' \
        --dev_file_name='dev.json' \
        --test_file_name='test.json' \
        --train_on_multi_events=True \
        --train_on_single_event=True \
        --event_type_weight='[1,1,0.5,0.5,0.2,0.1]' \
        --cost_weight_event_type=2.0 \
        --cost_weight_role=1.0 \
        --event_type_classes=6 \
        --parallel_decorate
}
