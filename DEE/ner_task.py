import torch
import logging
import os
import json
from torch.utils.data import TensorDataset
from collections import defaultdict

from .utils import default_load_json, default_dump_json, EPS, BERTChineseCharacterTokenizer
from .event_type import common_fields, event_type_fields_list
from .ner_model_transformer import BertForBasicNER, judge_ner_prediction
from .base_task import TaskSetting, BasePytorchTask


logger = logging.getLogger(__name__)


class NERExample(object):
    basic_entity_label = 'O'

    def __init__(self, guid, text, entity_range_span_types):
        self.guid = guid
        self.text = text
        self.num_chars = len(text)
        self.entity_range_span_types = sorted(entity_range_span_types, key=lambda x: x[0])

    def get_char_entity_labels(self):
        char_entity_labels = []
        char_idx = 0
        ent_idx = 0
        while ent_idx < len(self.entity_range_span_types):
            (ent_cid_s, ent_cid_e), ent_span, ent_type = self.entity_range_span_types[ent_idx]
            assert ent_cid_s < ent_cid_e <= self.num_chars

            if ent_cid_s > char_idx:
                char_entity_labels.append(NERExample.basic_entity_label)
                char_idx += 1
            elif ent_cid_s == char_idx:
                # tmp_ent_labels = [ent_type] * (ent_cid_e - ent_cid_s)
                tmp_ent_labels = ['B-' + ent_type] + ['I-' + ent_type] * (ent_cid_e - ent_cid_s - 1)
                char_entity_labels.extend(tmp_ent_labels)
                char_idx = ent_cid_e
                ent_idx += 1
            else:
                logger.error('Example GUID {}'.format(self.guid))
                logger.error('NER conflicts at char_idx {}, ent_cid_s {}'.format(char_idx, ent_cid_s))
                logger.error(self.text[char_idx - 20:char_idx + 20])
                logger.error(self.entity_range_span_types[ent_idx - 1:ent_idx + 1])
                raise Exception('Unexpected logic error')

        char_entity_labels.extend([NERExample.basic_entity_label] * (self.num_chars - char_idx))
        assert len(char_entity_labels) == self.num_chars

        return char_entity_labels

    @staticmethod
    def get_entity_label_list():
        visit_set = set()
        entity_label_list = [NERExample.basic_entity_label]

        for field in common_fields:
            if field not in visit_set:
                visit_set.add(field)
                entity_label_list.extend(['B-' + field, 'I-' + field])

        for event_name, fields in event_type_fields_list:
            for field in fields:
                if field not in visit_set:
                    visit_set.add(field)
                    entity_label_list.extend(['B-' + field, 'I-' + field])

        return entity_label_list

    def __repr__(self):
        ex_str = 'NERExample(guid={}, text={}, entity_info={}'.format(
            self.guid, self.text, str(self.entity_range_span_types)
        )
        return ex_str


def load_ner_dataset(dataset_json_path):
    total_ner_examples = []
    annguid2detail_align_info = default_load_json(dataset_json_path)
    for annguid, detail_align_info in annguid2detail_align_info.items():
        sents = detail_align_info['sentences']
        ann_valid_mspans = detail_align_info['ann_valid_mspans']
        ann_valid_dranges = detail_align_info['ann_valid_dranges']
        ann_mspan2guess_field = detail_align_info['ann_mspan2guess_field']
        ann_mspan2dranges = detail_align_info['ann_mspan2dranges']
        recguid_eventname_eventdict_list = detail_align_info['recguid_eventname_eventdict_list']
        assert len(ann_mspan2dranges) == len(ann_valid_mspans)
        event_type = recguid_eventname_eventdict_list[0][1]

        sent_idx2mrange_mspan_mfield_tuples = {}
        for mspan, dranges in ann_mspan2dranges.items():
            for drange in dranges:
                sent_idx, char_s, char_e = drange
                sent_mrange = (char_s, char_e)

                sent_text = sents[sent_idx]
                assert sent_text[char_s: char_e] == mspan

                guess_field = ann_mspan2guess_field[mspan]

                if sent_idx not in sent_idx2mrange_mspan_mfield_tuples:
                    sent_idx2mrange_mspan_mfield_tuples[sent_idx] = []
                sent_idx2mrange_mspan_mfield_tuples[sent_idx].append((sent_mrange, mspan, guess_field))

        for sent_idx in range(len(sents)):
            sent_text = sents[sent_idx]
            if sent_idx in sent_idx2mrange_mspan_mfield_tuples:
                mrange_mspan_mfield_tuples = sent_idx2mrange_mspan_mfield_tuples[sent_idx]
            else:
                mrange_mspan_mfield_tuples = []
            total_ner_examples.append(
                NERExample('{}-{}'.format(annguid, sent_idx),
                           sent_text,
                           mrange_mspan_mfield_tuples)
            )
    return total_ner_examples


class NERFeature(object):
    def __init__(self, input_ids, input_masks, segment_ids, label_ids, seq_len=None):
        self.input_ids = input_ids
        self.input_masks = input_masks
        self.segment_ids = segment_ids
        self.label_ids = label_ids
        self.seq_len = seq_len

    def __repr__(self):
        fea_strs = ['NERFeature(real_seq_len={}'.format(self.seq_len), ]
        info_template = '  {:5} {:9} {:5} {:7} {:7}'
        fea_strs.append(info_template.format(
            'index', 'input_ids', 'masks', 'seg_ids', 'lbl_ids'
        ))
        max_print_len = 10
        idx = 0
        for tid, mask, segid, lid in zip(
                self.input_ids, self.input_masks, self.segment_ids, self.label_ids):
            fea_strs.append(info_template.format(
                idx, tid, mask, segid, lid
            ))
            idx += 1
            if idx >= max_print_len:
                break
        fea_strs.append(info_template.format(
            '...', '...', '...', '...', '...'
        ))
        fea_strs.append(')')

        fea_str = '\n'.join(fea_strs)
        return fea_str


class NERFeatureConverter(object):
    def __init__(self, entity_label_list, max_seq_len, tokenizer, include_cls=True, include_sep=True):
        self.entity_label_list = entity_label_list
        self.max_seq_len = max_seq_len  # used to normalize sequence length
        self.tokenizer = tokenizer
        self.entity_label2index = {  # for entity label to label index mapping
            entity_label: idx for idx, entity_label in enumerate(self.entity_label_list)
        }

        self.include_cls = include_cls
        self.include_sep = include_sep

        # used to track how many examples have been truncated
        self.truncate_count = 0
        # used to track the maximum length of input sentences
        self.data_max_seq_len = -1

    def convert_example_to_feature(self, ner_example, log_flag=False):
        ex_tokens = self.tokenizer.char_tokenize(ner_example.text)
        ex_entity_labels = ner_example.get_char_entity_labels()

        assert len(ex_tokens) == len(ex_entity_labels)

        # get valid token sequence length
        valid_token_len = self.max_seq_len
        if self.include_cls:
            valid_token_len -= 1
        if self.include_sep:
            valid_token_len -= 1

        # truncate according to max_seq_len and record some statistics
        self.data_max_seq_len = max(self.data_max_seq_len, len(ex_tokens))
        if len(ex_tokens) > valid_token_len:
            ex_tokens = ex_tokens[:valid_token_len]
            ex_entity_labels = ex_entity_labels[:valid_token_len]

            self.truncate_count += 1

        basic_label_index = self.entity_label2index[NERExample.basic_entity_label]

        # add bert-specific token
        if self.include_cls:
            fea_tokens = ['[CLS]']
            fea_token_labels = [NERExample.basic_entity_label]
            fea_label_ids = [basic_label_index]
        else:
            fea_tokens = []
            fea_token_labels = []
            fea_label_ids = []

        for token, ent_label in zip(ex_tokens, ex_entity_labels):
            fea_tokens.append(token)
            fea_token_labels.append(ent_label)

            if ent_label in self.entity_label2index:
                fea_label_ids.append(self.entity_label2index[ent_label])
            else:
                fea_label_ids.append(basic_label_index)

        if self.include_sep:
            fea_tokens.append('[SEP]')
            fea_token_labels.append(NERExample.basic_entity_label)
            fea_label_ids.append(basic_label_index)

        assert len(fea_tokens) == len(fea_token_labels) == len(fea_label_ids) <= self.max_seq_len

        fea_input_ids = self.tokenizer.convert_tokens_to_ids(fea_tokens)
        fea_seq_len = len(fea_input_ids)
        fea_segment_ids = [0] * fea_seq_len
        fea_masks = [1] * fea_seq_len

        # feature is padded to max_seq_len, but fea_seq_len is the real length
        while len(fea_input_ids) < self.max_seq_len:
            fea_input_ids.append(0)
            fea_label_ids.append(0)
            fea_masks.append(0)
            fea_segment_ids.append(0)

        assert len(fea_input_ids) == len(fea_label_ids) == len(fea_masks) == len(fea_segment_ids) == self.max_seq_len

        if log_flag:
            logger.info("*** Example ***")
            logger.info("guid: %s" % ner_example.guid)
            info_template = '{:8} {:4} {:2} {:2} {:2} {}'
            logger.info(info_template.format(
                'TokenId', 'Token', 'Mask', 'SegId', 'LabelId', 'Label'
            ))
            for tid, token, mask, segid, lid, label in zip(
                    fea_input_ids, fea_tokens, fea_masks,
                    fea_segment_ids, fea_label_ids, fea_token_labels):
                logger.info(info_template.format(
                    tid, token, mask, segid, lid, label
                ))
            if len(fea_input_ids) > len(fea_tokens):
                sid = len(fea_tokens)
                logger.info(info_template.format(
                    fea_input_ids[sid], '[PAD]', fea_masks[sid], fea_segment_ids[sid], fea_label_ids[sid], 'O')
                            + ' x {}'.format(len(fea_input_ids) - len(fea_tokens)))

        return NERFeature(fea_input_ids, fea_masks, fea_segment_ids, fea_label_ids, seq_len=fea_seq_len)

    def __call__(self, ner_examples, log_example_num=0):
        """Convert examples to features suitable for ner models"""
        self.truncate_count = 0
        self.data_max_seq_len = -1
        ner_features = []

        for ex_index, ner_example in enumerate(ner_examples):
            if ex_index < log_example_num:
                ner_feature = self.convert_example_to_feature(ner_example, log_flag=True)
            else:
                ner_feature = self.convert_example_to_feature(ner_example, log_flag=False)

            ner_features.append(ner_feature)

        logger.info('{} examples in total, {} truncated example, max_sent_len={}'.format(
            len(ner_examples), self.truncate_count, self.data_max_seq_len
        ))

        return ner_features


def convert_ner_features_to_dataset(ner_features, Test = False):
    all_input_ids = torch.tensor([f.input_ids for f in ner_features], dtype=torch.long)
    # very important to use the mask type of uint8 to support advanced indexing
    all_input_masks = torch.tensor([f.input_masks for f in ner_features], dtype=torch.uint8)
    all_segment_ids = torch.tensor([f.segment_ids for f in ner_features], dtype=torch.long)
    all_label_ids = torch.tensor([f.label_ids for f in ner_features], dtype=torch.long)
    all_seq_len = torch.tensor([f.seq_len for f in ner_features], dtype=torch.long)
    if Test:
        ner_tensor_dataset = all_input_ids, all_input_masks, all_segment_ids, all_label_ids, all_seq_len
    else:
        ner_tensor_dataset = TensorDataset(all_input_ids, all_input_masks, all_segment_ids, all_label_ids, all_seq_len)
    return ner_tensor_dataset


class NERTaskSetting(TaskSetting):
    def __init__(self, **kwargs):
        ner_key_attrs = []
        ner_attr_default_pairs = [
            ('bert_model', 'bert-base-chinese'),
            ('train_file_name', 'train.json'),
            ('dev_file_name', 'dev.json'),
            ('test_file_name', 'test.json'),
            ('max_seq_len', 128),
            ('max_sent_len', 128),
            ('max_sent_num', 64),
            ('train_batch_size', 32),
            ('eval_batch_size', 64),
            ('learning_rate', 2e-5),
            ('num_train_epochs', 30.0),
            ('warmup_proportion', 0.1),
            ('no_cuda', False),
            ('local_rank', -1),
            ('seed', 99),
            ('gradient_accumulation_steps', 1),
            ('optimize_on_cpu', True),
            ('fp16', False),
            ('loss_scale', 128),
            ('cpt_file_name', 'ner_task.cpt'),
            ('summary_dir_name', '/tmp/summary'),
            ('hidden_size', 768),
            ('dropout', 0.1),
            ('ff_size', 1024),  # feed-forward mid layer size
            ('num_tf_layers', 4),  # transformenum_tf_layersr layer number
            ('use_crf_layer', True),  # whether to use CRF Layer
        ]
        super(NERTaskSetting, self).__init__(ner_key_attrs, ner_attr_default_pairs, **kwargs)


class NERTask(BasePytorchTask):
    """Named Entity Recognition Task"""

    def __init__(self, setting,
                 load_train=True, load_dev=True, load_test=True,
                 build_model=True, parallel_decorate=True,
                 resume_model=False, resume_optimizer=False, Test = False):
        super(NERTask, self).__init__(setting)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logging('Initializing {}'.format(self.__class__.__name__))

        # initialize entity label list
        self.entity_label_list = NERExample.get_entity_label_list()
        # initialize tokenizer
        self.tokenizer = BERTChineseCharacterTokenizer.from_pretrained(self.setting.bert_model)
        # initialize feature converter
        self.setting.vocab_size = len(self.tokenizer.vocab)
        self.feature_converter_func = NERFeatureConverter(
            self.entity_label_list, self.setting.max_seq_len, self.tokenizer
        )
        self.entity_label2index = {  # for entity label to label index mapping
            entity_label: idx for idx, entity_label in enumerate(self.entity_label_list)
        }
        self.index2entity_lable = {
            value:key for key , value in self.entity_label2index.items()
        }

        # load data
        self._load_data(
            load_ner_dataset, self.feature_converter_func, convert_ner_features_to_dataset,
            load_train=load_train, load_dev=load_dev, load_test=load_test
        )

        # build model
        self.setting.num_entity_labels = len(self.entity_label_list)
        if build_model:
            self.model = BertForBasicNER.from_pretrained(self.setting.bert_model, len(self.entity_label_list))
            self.setting.update_by_dict(self.model.config.__dict__)  # BertConfig dictionary
            self._decorate_model(parallel_decorate=parallel_decorate)

        # prepare optimizer
        if build_model and load_train:
            self._init_bert_optimizer()

        # resume option
        if build_model and (resume_model or resume_optimizer):
            self.resume_checkpoint(resume_model=resume_model, resume_optimizer=resume_optimizer)

        self.logging('Successfully initialize {}'.format(self.__class__.__name__))

    def reload_data(self, data_type='return', file_name=None, file_path=None, **kwargs):
        """ Either file_name or file_path needs to be provided,
            data_type: return (default), return (examples, features, dataset)
                       train, override self.train_xxx
                       dev, override self.dev_xxx
                       test, override self.test_xxx
        """
        return super(NERTask, self).reload_data(
            load_ner_dataset, self.feature_converter_func, convert_ner_features_to_dataset,
            data_type=data_type, file_name=file_name, file_path=file_path,
        )

    def convert_single_example_to_feature(self, text, include_cls = True, include_sep = True):
        ex_tokens = self.tokenizer.char_tokenize(text)
        valid_token_len = self.setting.max_seq_len

        max_seq_len = self.setting.max_seq_len
        if include_cls:
            valid_token_len -= 1
        if include_sep:
            valid_token_len -= 1
        if len(ex_tokens) > valid_token_len:
            ex_tokens = ex_tokens[:valid_token_len]

        basic_label_index = self.entity_label2index[NERExample.basic_entity_label]

        if include_cls:
            fea_tokens = ['[CLS]']
            fea_token_labels = [NERExample.basic_entity_label]
            fea_label_ids = [basic_label_index]
        else:
            fea_tokens = []
            fea_token_labels = []
            fea_label_ids = []

        for token in ex_tokens:
            fea_tokens.append(token)

        if include_sep:
            fea_tokens.append('[SEP]')

        fea_input_ids = self.tokenizer.convert_tokens_to_ids(fea_tokens)
        fea_seq_len = len(fea_input_ids)
        fea_segment_ids = [0] * fea_seq_len
        fea_masks = [1] * fea_seq_len

        # feature is padded to max_seq_len, but fea_seq_len is the real length
        while len(fea_input_ids) < max_seq_len:
            fea_input_ids.append(0)
            fea_masks.append(0)
            fea_segment_ids.append(0)
        fea_label_ids = [0] * max_seq_len
        assert len(fea_input_ids) == len(fea_label_ids) == len(fea_masks) == len(fea_segment_ids) == max_seq_len
        return NERFeature(fea_input_ids, fea_masks, fea_segment_ids, fea_label_ids, seq_len=fea_seq_len)

    def train(self):
        self.logging('='*20 + 'Start Training' + '='*20)
        self.base_train(get_ner_loss_on_batch, self.eval_function)

    ### test
    def test(self, event_type, see_data):
        self.logging('='*20 + 'Start Testing' + '='*20)
        data_dir = "./Data/"
        file_name = "{}.json".format(see_data)
        dataset_json_path = data_dir + file_name
        with open(dataset_json_path, 'r', encoding='utf-8') as fin:
            tmp_json = json.load(fin)
        for annguid, detail_align_info in tmp_json:
            print(annguid)
            recguid_eventname_eventdict_list = detail_align_info['recguid_eventname_eventdict_list']
            doc_event_type = recguid_eventname_eventdict_list[0][1]
            if doc_event_type == event_type:
                sents = detail_align_info['sentences']
                entity_list_result = []
                for sent in sents:
                    text_feature = self.convert_single_example_to_feature(text=sent)
                    batch = convert_ner_features_to_dataset([text_feature], Test=True)
                    # value = [[(pred_label, gold_label, token_mask), ...], ...]
                    batch_info = self.base_test(batch, get_ner_pred_on_batch)
                    sen_length = len(sent)
                    entity_result = batch_info.cpu().data.numpy().tolist()
                    tags = [self.index2entity_lable[idx[0]] for idx in entity_result[0]]
                    json_result = result_to_json(sent, tags, id = annguid)
                    # print(json_result, "\n")
                    entity_list_result.append(json_result)
                assert len(sents) == len(entity_list_result)
                detail_align_info['entities'] = entity_list_result
                info = [annguid, detail_align_info]
                write_test_result(info,event_type, see_data)


    # def get_local_context_info(self, doc_batch_dict, train_flag=False, use_gold_span=False):
    #     label_key = 'doc_token_labels'
    #     if train_flag or use_gold_span:
    #         assert label_key in doc_batch_dict
    #         need_label_flag = True
    #     else:
    #         need_label_flag = False
    #
    #     if need_label_flag:
    #         doc_token_labels_list = self.adjust_token_label(doc_batch_dict[label_key])
    #     else:
    #         doc_token_labels_list = None
    #
    #     batch_size = len(doc_batch_dict['ex_idx'])
    #     doc_token_ids_list = doc_batch_dict['doc_token_ids']
    #     doc_token_masks_list = doc_batch_dict['doc_token_masks']
    #     valid_sent_num_list = doc_batch_dict['valid_sent_num']
    #
    #     # transform doc_batch into sent_batch
    #     ner_batch_idx_start_list = [0]
    #     ner_token_ids = []
    #     ner_token_masks = []
    #     ner_token_labels = [] if need_label_flag else None
    #     for batch_idx, valid_sent_num in enumerate(valid_sent_num_list):
    #         idx_start = ner_batch_idx_start_list[-1]
    #         idx_end = idx_start + valid_sent_num
    #         ner_batch_idx_start_list.append(idx_end)
    #
    #         ner_token_ids.append(doc_token_ids_list[batch_idx])
    #         ner_token_masks.append(doc_token_masks_list[batch_idx])
    #         if need_label_flag:
    #             ner_token_labels.append(doc_token_labels_list[batch_idx])
    #
    #     # [ner_batch_size, norm_sent_len]
    #     ner_token_ids = torch.cat(ner_token_ids, dim=0)
    #     ner_token_masks = torch.cat(ner_token_masks, dim=0)
    #     if need_label_flag:
    #         ner_token_labels = torch.cat(ner_token_labels, dim=0)
    #
    #     # get ner output
    #     ner_token_emb, ner_loss, ner_token_preds = self.model(
    #         ner_token_ids, ner_token_masks, label_ids=ner_token_labels,
    #         train_flag=train_flag, decode_flag=not use_gold_span,
    #     )

    def eval_function(self, eval_dataset,  eval_save_prefix='', pgm_return_flag=False):
        self.logging('eval size {}'.format(len(eval_dataset)))
        total_seq_pgm = self.get_total_prediction(eval_dataset, load_model = False)
        num_examples, max_seq_len, _ = total_seq_pgm.size()

        # 2. collect per-entity-label tp, fp, fn counts
        ent_lid2tp_cnt = defaultdict(lambda: 0)
        ent_lid2fp_cnt = defaultdict(lambda: 0)
        ent_lid2fn_cnt = defaultdict(lambda: 0)
        for bid in range(num_examples):
            seq_pgm = total_seq_pgm[bid]  # [max_seq_len, 3]
            seq_pred = seq_pgm[:, 0]  # [max_seq_len]
            seq_gold = seq_pgm[:, 1]
            seq_mask = seq_pgm[:, 2]

            seq_pred_lid = seq_pred[seq_mask == 1]  # [seq_len]
            seq_gold_lid = seq_gold[seq_mask == 1]
            ner_tp_set, ner_fp_set, ner_fn_set = judge_ner_prediction(seq_pred_lid, seq_gold_lid)
            for ent_lid2cnt, ex_ner_set in [
                (ent_lid2tp_cnt, ner_tp_set),
                (ent_lid2fp_cnt, ner_fp_set),
                (ent_lid2fn_cnt, ner_fn_set)
            ]:
                for ent_idx_s, ent_idx_e, ent_lid in ex_ner_set:
                    ent_lid2cnt[ent_lid] += 1

        # 3. calculate per-entity-label metrics and collect global counts
        ent_label_eval_infos = []
        g_ner_tp_cnt = 0
        g_ner_fp_cnt = 0
        g_ner_fn_cnt = 0
        # Entity Label Id, 0 for others, odd for BEGIN-ENTITY, even for INSIDE-ENTITY
        # using odd is enough to represent the entity type
        for ent_lid in range(1, len(self.entity_label_list), 2):
            el_name = self.entity_label_list[ent_lid]
            el_tp_cnt, el_fp_cnt, el_fn_cnt = ent_lid2tp_cnt[ent_lid], ent_lid2fp_cnt[ent_lid], ent_lid2fn_cnt[ent_lid]

            el_pred_cnt = el_tp_cnt + el_fp_cnt
            el_gold_cnt = el_tp_cnt + el_fn_cnt
            el_prec = el_tp_cnt / el_pred_cnt if el_pred_cnt > 0 else 0
            el_recall = el_tp_cnt / el_gold_cnt if el_gold_cnt > 0 else 0
            el_f1 = 2 / (1 / el_prec + 1 / el_recall) if el_prec > EPS and el_recall > EPS else 0

            # per-entity-label evaluation info
            el_eval_info = {
                'entity_label_indexes': (ent_lid, ent_lid + 1),
                'entity_label': el_name[2:],  # omit 'B-' prefix
                'ner_tp_cnt': el_tp_cnt,
                'ner_fp_cnt': el_fp_cnt,
                'ner_fn_cnt': el_fn_cnt,
                'ner_prec': el_prec,
                'ner_recall': el_recall,
                'ner_f1': el_f1,
            }
            ent_label_eval_infos.append(el_eval_info)

            # collect global count info
            g_ner_tp_cnt += el_tp_cnt
            g_ner_fp_cnt += el_fp_cnt
            g_ner_fn_cnt += el_fn_cnt

        # 4. summarize total evaluation info
        g_ner_pred_cnt = g_ner_tp_cnt + g_ner_fp_cnt
        g_ner_gold_cnt = g_ner_tp_cnt + g_ner_fn_cnt
        g_ner_prec = g_ner_tp_cnt / g_ner_pred_cnt if g_ner_pred_cnt > 0 else 0
        g_ner_recall = g_ner_tp_cnt / g_ner_gold_cnt if g_ner_gold_cnt > 0 else 0
        g_ner_f1 = 2 / (1 / g_ner_prec + 1 / g_ner_recall) if g_ner_prec > EPS and g_ner_recall > EPS else 0

        total_eval_info = {
            'eval_name': eval_save_prefix,
            'num_examples': num_examples,
            'ner_tp_cnt': g_ner_tp_cnt,
            'ner_fp_cnt': g_ner_fp_cnt,
            'ner_fn_cnt': g_ner_fn_cnt,
            'ner_prec': g_ner_prec,
            'ner_recall': g_ner_recall,
            'ner_f1': g_ner_f1,
            'per_ent_label_eval': ent_label_eval_infos
        }

        self.logging('Evaluation Results\n{:.300s} ...'.format(json.dumps(total_eval_info, indent=4)))

        if eval_save_prefix:
            eval_res_fp = os.path.join(self.setting.output_dir,
                                       '{}.eval'.format(eval_save_prefix))
            self.logging('Dump eval results into {}'.format(eval_res_fp))
            default_dump_json(total_eval_info, eval_res_fp)
        return g_ner_f1

    def eval(self, eval_save_prefix='', pgm_return_flag=False):
        eval_dataset = self.dev_dataset
        self.logging('='*20 + 'Start Evaluation' + '='*10)
        # 1. get total prediction info
        # pgm denotes (pred_label, gold_label, token_mask)
        # size = [num_examples, max_seq_len, 3]
        # value = [[(pred_label, gold_label, token_mask), ...], ...]
        self.logging('eval size {}'.format(len(eval_dataset)))
        total_seq_pgm = self.get_total_prediction(eval_dataset, load_model=True)
        num_examples, max_seq_len, _ = total_seq_pgm.size()

        pre_num = 0
        gold_num = 0
        right_num = 0
        for bid in range(num_examples):
            seq_pgm = total_seq_pgm[bid]  # [max_seq_len, 3]
            seq_pred = seq_pgm[:, 0]  # [max_seq_len]
            seq_gold = seq_pgm[:, 1]
            seq_mask = seq_pgm[:, 2]
            #
            seq_mask = [seq for seq in seq_mask if seq == 1]
            seq_len = len(seq_mask)
            seq_pre = seq_pred[1:seq_len]
            seq_gold = seq_gold[1:seq_len]

            for pre, gold in zip(seq_pre, seq_gold):
                if pre != 0:
                    pre_num += 1
                if gold != 0:
                    gold_num += 1
                    if pre == gold:
                        right_num += 1


        p = right_num/pre_num
        r = right_num/gold_num
        f = (p * r)/(p + r) * 2
        total_eval_info = {
            'eval_name': eval_save_prefix,
            'num_examples': num_examples,
            'ner_prec': p,
            'ner_recall': r,
            'ner_f1': f,
        }

        self.logging('Evaluation Results\n{:.300s} ...'.format(json.dumps(total_eval_info, indent=4)))

        if eval_save_prefix:
            eval_res_fp = os.path.join(self.setting.output_dir,
                                       '{}.eval'.format(eval_save_prefix))
            self.logging('Dump eval results into {}'.format(eval_res_fp))
            default_dump_json(total_eval_info, eval_res_fp)

        if pgm_return_flag:
            return total_seq_pgm
        else:
            return total_eval_info

    def get_total_prediction(self, eval_dataset, load_model):
        self.logging('='*20 + 'Get Total Prediction' + '='*20)
        total_pred_gold_mask = self.base_eval(
            eval_dataset, get_ner_pred_on_batch, load_model, reduce_info_type='none'
        )
        # torch.Tensor(dtype=torch.long, device='cpu')
        # size = [batch_size, seq_len, 3]
        # value = [[(pred_label, gold_label, token_mask), ...], ...]
        return total_pred_gold_mask


def normalize_batch_seq_len(input_seq_lens, *batch_seq_tensors):
    batch_max_seq_len = input_seq_lens.max().item()
    normed_tensors = []
    for batch_seq_tensor in batch_seq_tensors:
        if batch_seq_tensor.dim() == 2:
            normed_tensors.append(batch_seq_tensor[:, :batch_max_seq_len])
        elif batch_seq_tensor.dim() == 1:
            normed_tensors.append(batch_seq_tensor)
        else:
            raise Exception('Unsupported batch_seq_tensor dimension {}'.format(batch_seq_tensor.dim()))

    return normed_tensors


def prepare_ner_batch(batch, resize_len=True):
    # prepare batch
    input_ids, input_masks, segment_ids, label_ids, input_lens = batch
    if resize_len:
        input_ids, input_masks, segment_ids, label_ids = normalize_batch_seq_len(
            input_lens, input_ids, input_masks, segment_ids, label_ids
        )

    return input_ids, input_masks, segment_ids, label_ids


def get_ner_loss_on_batch(ner_task, batch):
    input_ids, input_masks, segment_ids, label_ids = prepare_ner_batch(batch, resize_len=True)
    _, loss, _ = ner_task.model(input_ids, input_masks, label_ids)

    return loss


def get_ner_metrics_on_batch(ner_task, batch):
    input_ids, input_masks, segment_ids, label_ids = prepare_ner_batch(batch, resize_len=True)
    batch_metrics = ner_task.model(input_ids, input_masks,
                                   token_type_ids=segment_ids,
                                   label_ids=label_ids,
                                   eval_flag=True,
                                   eval_for_metric=True)

    return batch_metrics


def get_ner_pred_on_batch(ner_task, batch):
    # important to set resize_len to False to maintain the same seq len between batches
    input_ids, input_masks, segment_ids, label_ids = prepare_ner_batch(batch, resize_len=False)
    batch_seq_pred_gold_mask = ner_task.model(input_ids, input_masks,
                                            #   token_type_ids=segment_ids,
                                              label_ids=label_ids,
                                              eval_flag=True,
                                              eval_for_metric=False)
    # size = [batch_size, max_seq_len, 3]
    # value = [[(pred_label, gold_label, token_mask), ...], ...]
    torch.cuda.empty_cache()
    return batch_seq_pred_gold_mask


def result_to_json(string, tags, id):
    tags = tags[1:len(string)+1]
    pos_idx = 0
    entity = ""
    entity_list = []
    start_inx = -1
    for tag in tags:
        if tag[0] == "B":
            if entity == "":
                entity = string[pos_idx]
                entity_type = tag.split("-")[1]
                start_inx = pos_idx
                pos_idx += 1
            else:
                end_inx = start_inx + len(entity)
                pos = (start_inx, end_inx)
                entity_list.append([pos, entity, entity_type])
                entity = string[pos_idx]
                start_inx = pos_idx
                entity_type = tag.split("-")[1]
                pos_idx += 1
        elif tag[0] == "I":
            if start_inx == -1:
                start_inx = pos_idx
                entity_type = tag.split("-")[1]
            entity += string[pos_idx]
            pos_idx += 1
        else:
            if entity != "":
                end_inx = start_inx + len(entity)
                pos = (start_inx, end_inx)
                entity_list.append([pos, entity, entity_type])
                pos_idx += 1
                entity = ""
            else:
                pos_idx += 1
    return entity_list

def write_test_result(data,event_type, see_data):
    data_dir = "./Data/"
    file_name = "{}_SEE_{}.json".format(see_data, event_type)
    file_path = os.path.join(data_dir, file_name)
    with open(file_path, 'a', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")
