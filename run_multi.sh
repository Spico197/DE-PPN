#!/bin/bash

set -vx

CUDA="0,1,2,3"
NUM_GPUS=4

{
    CUDA_VISIBLE_DEVICES=${CUDA} bash train_multi.sh ${NUM_GPUS} \
        --task_name='debug-SetPre4DEE_1215_with_crf' \
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
        --parallel_decorate
}
