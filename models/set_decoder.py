import torch.nn as nn
import torch
from transformers.modeling_bert import BertIntermediate, BertOutput, BertAttention, BertLayerNorm, BertSelfAttention


class SetDecoder(nn.Module):
    def __init__(self, config, num_generated_triplets, num_layers, event_type_classes, return_intermediate=False):
        super().__init__()
        self.return_intermediate = return_intermediate
        self.num_generated_triplets = num_generated_triplets
        self.layers = nn.ModuleList([DecoderLayer(config) for _ in range(num_layers)])
        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.query_embed = nn.Embedding(num_generated_triplets, config.hidden_size)
        self.decoder2class = nn.Linear(config.hidden_size, event_type_classes)
        self.decoder2span = nn.Linear(config.hidden_size, 4)

        self.head_start_metric_1 = nn.Linear(config.hidden_size, config.hidden_size)
        self.head_end_metric_1 = nn.Linear(config.hidden_size, config.hidden_size)
        self.tail_start_metric_1 = nn.Linear(config.hidden_size, config.hidden_size)
        self.tail_end_metric_1 = nn.Linear(config.hidden_size, config.hidden_size)
        self.head_start_metric_2 = nn.Linear(config.hidden_size, config.hidden_size)
        self.head_end_metric_2 = nn.Linear(config.hidden_size, config.hidden_size)
        self.tail_start_metric_2 = nn.Linear(config.hidden_size, config.hidden_size)
        self.tail_end_metric_2 = nn.Linear(config.hidden_size, config.hidden_size)
        self.head_start_metric_3 = nn.Linear(config.hidden_size, 1, bias=False)
        self.head_end_metric_3 = nn.Linear(config.hidden_size, 1, bias=False)
        self.tail_start_metric_3 = nn.Linear(config.hidden_size, 1, bias=False)
        self.tail_end_metric_3 = nn.Linear(config.hidden_size, 1, bias=False)
        torch.nn.init.orthogonal_(self.head_start_metric_1.weight, gain=1)
        torch.nn.init.orthogonal_(self.head_end_metric_1.weight, gain=1)
        torch.nn.init.orthogonal_(self.tail_start_metric_1.weight, gain=1)
        torch.nn.init.orthogonal_(self.tail_end_metric_1.weight, gain=1)
        torch.nn.init.orthogonal_(self.head_start_metric_2.weight, gain=1)
        torch.nn.init.orthogonal_(self.head_end_metric_2.weight, gain=1)
        torch.nn.init.orthogonal_(self.tail_start_metric_2.weight, gain=1)
        torch.nn.init.orthogonal_(self.tail_end_metric_2.weight, gain=1)





        # self.head_start_metric = nn.Parameter(torch.randn(config.hidden_size, config.hidden_size))
        # self.head_end_metric = nn.Parameter(torch.randn(config.hidden_size, config.hidden_size))
        # self.tail_start_metric = nn.Parameter(torch.randn(config.hidden_size, config.hidden_size))
        # self.tail_end_metric = nn.Parameter(torch.randn(config.hidden_size, config.hidden_size))
        # torch.nn.init.orthogonal_(self.head_start_metric.data, gain=1)
        # torch.nn.init.orthogonal_(self.head_end_metric.data, gain=1)
        # torch.nn.init.orthogonal_(self.tail_start_metric.data, gain=1)
        # torch.nn.init.orthogonal_(self.tail_end_metric.data, gain=1)

        torch.nn.init.orthogonal_(self.query_embed.weight, gain=1)
        # self.query_embed.weight.requires_grad = False


    def forward(self, encoder_hidden_states):
        print(encoder_hidden_states.size(), "*")
        bsz = encoder_hidden_states.size()[0]
        hidden_states = self.query_embed.weight.unsqueeze(0).repeat(bsz, 1, 1)
        hidden_states = self.dropout(self.LayerNorm(hidden_states))
        all_hidden_states = ()
        for i, layer_module in enumerate(self.layers):
            if self.return_intermediate:
                all_hidden_states = all_hidden_states + (hidden_states,)
            layer_outputs = layer_module(
                hidden_states, encoder_hidden_states
            )
            hidden_states = layer_outputs[0]
        # if self.return_intermediate:
        #     all_hidden_states = all_hidden_states + (hidden_states,)
        # outputs = (hidden_states,)
        # if self.return_intermediate:
        #     outputs = outputs + (all_hidden_states,)
        # hidden_states = torch.tanh(hidden_states)
        class_logits = self.decoder2class(hidden_states)
        # head_start_logits = torch.matmul(torch.matmul(hidden_states, self.head_start_metric),
        #                                  encoder_hidden_states.permute(0, 2, 1))
        # head_end_logits = torch.matmul(torch.matmul(hidden_states, self.head_end_metric),
        #                                  encoder_hidden_states.permute(0, 2, 1))
        # tail_start_logits = torch.matmul(torch.matmul(hidden_states, self.tail_start_metric),
        #                                  encoder_hidden_states.permute(0, 2, 1))
        # tail_end_logits = torch.matmul(torch.matmul(hidden_states, self.tail_end_metric),
        #                                  encoder_hidden_states.permute(0, 2, 1))


        head_start_logits = self.head_start_metric_3(torch.tanh(
            self.head_start_metric_1(hidden_states).unsqueeze(2) + self.head_start_metric_2(
                encoder_hidden_states).unsqueeze(1))).squeeze()
        head_end_logits = self.head_end_metric_3(torch.tanh(
            self.head_end_metric_1(hidden_states).unsqueeze(2) + self.head_end_metric_2(
                encoder_hidden_states).unsqueeze(1))).squeeze()
        tail_start_logits = self.tail_start_metric_3(torch.tanh(
            self.tail_start_metric_1(hidden_states).unsqueeze(2) + self.tail_start_metric_2(
                encoder_hidden_states).unsqueeze(1))).squeeze()
        tail_end_logits = self.tail_end_metric_3(torch.tanh(
            self.tail_end_metric_1(hidden_states).unsqueeze(2) + self.tail_end_metric_2(
                encoder_hidden_states).unsqueeze(1))).squeeze()

        # span_logits = torch.tanh(res_logits) + self.decoder2span(encoder_hidden_states.unsqueeze(1))
        # span_logits = self.decoder2span(encoder_hidden_states.unsqueeze(1) + hidden_states.unsqueeze(2))
        # head_start_logits, head_end_logits, tail_start_logits, tail_end_logits = span_logits.split(1, dim=-1)
        # # head_start_logits = torch.tanh(head_start_similarity)
        # # plus will generate trivial result, since plus will not change the distributation of encoder_hidden_states according to different query
        print(head_start_logits.size())
        print(head_end_logits.size())
        return class_logits, head_start_logits, head_end_logits, tail_start_logits, tail_end_logits
        # return class_logits, span_logits


class DecoderLayer(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.attention = BertAttention(config)
        self.crossattention = BertAttention(config)
        self.intermediate = BertIntermediate(config)
        self.output = BertOutput(config)

    def forward(
        self,
        hidden_states,
        encoder_hidden_states,
        encoder_attention_mask = None
    ):
        self_attention_outputs = self.attention(hidden_states)
        attention_output = self_attention_outputs[0]
        outputs = self_attention_outputs[1:]  # add self attentions if we output attention weights

        encoder_batch_size, encoder_sequence_length, _ = encoder_hidden_states.size()
        encoder_hidden_shape = (encoder_batch_size, encoder_sequence_length)
        if encoder_attention_mask.dim() == 3:
            encoder_extended_attention_mask = encoder_attention_mask[:, None, :, :]
        elif encoder_attention_mask.dim() == 2:
            encoder_extended_attention_mask = encoder_attention_mask[:, None, None, :]
        else:
            raise ValueError(
                "Wrong shape for encoder_hidden_shape (shape {}) or encoder_attention_mask (shape {})".format(
                    encoder_hidden_shape, encoder_attention_mask.shape
                )
            )
        encoder_extended_attention_mask = (1.0 - encoder_extended_attention_mask) * -10000.0
        cross_attention_outputs = self.crossattention(
            hidden_states=attention_output, encoder_hidden_states=encoder_hidden_states,  encoder_attention_mask=encoder_extended_attention_mask
        )
        attention_output = cross_attention_outputs[0]
        outputs = outputs + cross_attention_outputs[1:]  # add cross attentions if we output attention weights

        intermediate_output = self.intermediate(attention_output)
        layer_output = self.output(intermediate_output, attention_output)
        outputs = (layer_output,) + outputs
        return outputs