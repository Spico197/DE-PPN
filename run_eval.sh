#!/bin/bash

set -vx

{
    CUDA_VISIBLE_DEVICES="1" python -u run_main.py \
        --task_name='SetPre4DEE_reprod_optim_new' \
        --use_bert=False \
        --start_epoch=86 \
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
        --skip_train=True \
        --re_eval_flag=True \
        --use_crf_layer=False
}
