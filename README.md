<div align="center">
  <h1>Document-level Event Extraction via Parallel Prediction Networks</h1>
  <a href="#overview">🧱 Overview</a> | <a href="#datasets">💾 Datasets</a> | <a href="#dependencies">🌴 Dependencies</a> | <a href="#quickstart">🚀 QuickStart</a> <br />
  <a href="#implementation-detail">🔍 Implementation Details</a> | <a href="#results">📋 Results</a> | <a href="#reference">💌 Reference</a>
</div>


<h2 id="overview">🧱 Overview</h2>

Code for the paper ["Document-level Event Extraction via Parallel Prediction Networks"](https://aclanthology.org/2021.acl-long.492/).

This repo is built on the [official codes](https://github.com/HangYang-NLP/DE-PPN).
The official codes are not available to run due to some bugs.
There are many important details and codes missing from the official repo.
I can't wait to have a try and test the performance, so I complete the missing part and create this repo.

This repo is still under construction, and the program is still running to reproduce the final results.
Due to the time limit, codes are not totally refactored to be more elegant, but I will work on it.
Once the final results are confirmed to be able to reproduce, this repo would be integrated into [[the DocEE Toolkit]](https://github.com/Spico197/DocEE) .

Please be aware that this is not a totally officially implementated version.
If you find any problems, do not hesitate to drop me an issue, or reach me by email.

<p align="center">
  <img src="./overview.png" alt="Photo" style="width=100%;">
</p>

<h2 id="datasets">💾 Datasets</h2>

`ChFinAnn` is downloaded from [Here](https://github.com/dolphin-zs/Doc2EDAG/blob/master/Data.zip).
Data preprocessing, sentence-level extraction and evaluation metrics follow [Doc2EDAG](https://github.com/dolphin-zs/Doc2EDAG).

<h2 id="dependencies">🌴 Dependencies</h2>

Python >= 3.7
- pytorch=1.7.1
- transformers=4.6.1
- tensorboardX=2.4
- numpy=1.20.3
- scipy=1.7.1
- tqdm=4.61.0

<h2 id="quickstart">🚀 QuickStart</h2>

Change `CUDA_VISIBLE_DEVICES` in `run.sh` and run:

```bash
# single GPU
$ nohup bash run_single.sh >deppn.log 2>&1 &

# multiple GPUs
## change `NUM_GPUS` and `CUDA` in `run_multi.sh`
$ nohup bash run_multi.sh >deppn_multi.log 2>&1 &
```

<h2 id="implementation-detail">🔍 Implementation Details</h2>

**Q:** How to construct the golden targets?
- ~~In `DEEFeature.extract_predicted_instances`, records with **all** `None` arguments are labelled as `0` (NULL event).~~
- For arguments, the last entity (`role4None_embed`) represents `NULL` entity and is used as a role placeholder.

**Q:** How to select the best checkpoint?
- I follow the Doc2EDAG and use the MicroF1 on development set as the best model selection criteria.


<h2 id="results">📋 Results</h2>

I've sync the codes with the latest official remote (d8d357c1e8503d2525e7af5ea1f6aac613f90e53), and here are the results.

The results of `Doc2EDAG` is from the original paper.

- Speed (4 * V100)

| Model  | Train (min/epoch) | Inference (docs/s) | Total Training Process (hours) |
| :----- | ----------------: | -----------------: | -----------------------------: |
| DE-PPN (bs=16, grad accum=4, eval bs=8) |             34.57  |               4.18  |                          74.02  |

- Main Results

<table>
<thead>
  <tr>
    <th rowspan="2">Models</th>
    <th colspan="3">EF</th>
    <th colspan="3">ER</th>
    <th colspan="3">EU</th>
    <th colspan="3">EO</th>
    <th colspan="3">EP</th>
    <th colspan="3">Overall Macro</th>
    <th colspan="3">Overall Micro</th>
  </tr>
  <tr>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
    <th>P</th>
    <th>R</th>
    <th>F1</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>Doc2EDAG</td>
    <td>77.1</td>
    <td>64.5</td>
    <td>70.2</td>
    <td>91.3</td>
    <td>83.6</td>
    <td>87.3</td>
    <td>80.2</td>
    <td>65.0</td>
    <td>71.8</td>
    <td>82.1</td>
    <td>69.0</td>
    <td>75.0</td>
    <td>80.0</td>
    <td>74.8</td>
    <td>77.3</td>
    <td></td>
    <td></td>
    <td>76.3</td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td>DE-PPN (Paper)</td>
    <td>78.2</td>
    <td>69.4</td>
    <td>73.5</td>
    <td>89.3</td>
    <td>85.6</td>
    <td>87.4</td>
    <td>69.7</td>
    <td>79.9</td>
    <td>74.4</td>
    <td>81.0</td>
    <td>71.3</td>
    <td>75.8</td>
    <td>83.8</td>
    <td>73.7</td>
    <td>78.4</td>
    <td></td>
    <td></td>
    <td>77.9</td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td>DE-PPN (use_sent_span_encoder=True)</td>
    <td>64.1</td>
    <td>54.2</td>
    <td>58.7</td>
    <td>84.8</td>
    <td>76.3</td>
    <td>80.3</td>
    <td>59.0</td>
    <td>49.5</td>
    <td>53.8</td>
    <td>63.3</td>
    <td>50.9</td>
    <td>56.4</td>
    <td>70.5</td>
    <td>55.3</td>
    <td>62.0</td>
    <td>68.3</td>
    <td>57.2</td>
    <td>62.2</td>
    <td>72.6</td>
    <td>59.5</td>
    <td>65.4</td>
  </tr>
  <tr>
    <td>DE-PPN (use_sent_span_encoder=False)</td>
    <td>67.2</td>
    <td>51.6</td>
    <td>58.4</td>
    <td>86.9</td>
    <td>67.4</td>
    <td>75.9</td>
    <td>61.8</td>
    <td>49.6</td>
    <td>55.1</td>
    <td>66.5</td>
    <td>50.4</td>
    <td>57.3</td>
    <td>71.9</td>
    <td>57.7</td>
    <td>64.0</td>
    <td>70.9</td>
    <td>55.3</td>
    <td>62.1</td>
    <td>74.2</td>
    <td>58.6</td>
    <td>65.5</td>
  </tr>
  <tr>
    <td>DE-PPN (d8d357 use_sent_span_encoder=False, use doc_sent_context in set_layers)</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
</tbody>
</table>

- S. & M. Results

<table>
<thead>
  <tr>
    <th rowspan="2">Models</th>
    <th colspan="2">EF</th>
    <th colspan="2">ER</th>
    <th colspan="2">EU</th>
    <th colspan="2">EO</th>
    <th colspan="2">EP</th>
    <th colspan="2">Overall Macro</th>
    <th colspan="2">Overall Micro</th>
  </tr>
  <tr>
    <th>S.</th>
    <th>M.</th>
    <th>S.</th>
    <th>M.</th>
    <th>S.</th>
    <th>M.</th>
    <th>S.</th>
    <th>M.</th>
    <th>S.</th>
    <th>M.</th>
    <th>S.</th>
    <th>M.</th>
    <th>S.</th>
    <th>M.</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>Doc2EDAG</td>
    <td>80.0</td>
    <td>61.3</td>
    <td>89.4</td>
    <td>68.4</td>
    <td>77.4</td>
    <td>64.6</td>
    <td>79.4</td>
    <td>69.5</td>
    <td>85.5</td>
    <td>72.5</td>
    <td>82.3</td>
    <td>67.3</td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td>DE-PPN (Paper)</td>
    <td>82.1</td>
    <td>63.5</td>
    <td>89.1</td>
    <td>70.5</td>
    <td>79.7</td>
    <td>66.7</td>
    <td>80.6</td>
    <td>69.6</td>
    <td>88.0</td>
    <td>73.2</td>
    <td>83.9</td>
    <td>68.7</td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td>DE-PPN (use_sent_span_encoder=True)</td>
    <td>68.9</td>
    <td>49.0</td>
    <td>83.2</td>
    <td>56.0</td>
    <td>60.0</td>
    <td>45.7</td>
    <td>67.8</td>
    <td>41.7</td>
    <td>75.9</td>
    <td>53.7</td>
    <td>71.2</td>
    <td>49.2</td>
    <td>77.0</td>
    <td>52.2</td>
  </tr>
  <tr>
    <td>DE-PPN (use_sent_span_encoder=False)</td>
    <td>67.2</td>
    <td>49.8</td>
    <td>77.9</td>
    <td>58.9</td>
    <td>62.7</td>
    <td>45.2</td>
    <td>64.4</td>
    <td>48.3</td>
    <td>74.6</td>
    <td>57.7</td>
    <td>69.3</td>
    <td>52.0</td>
    <td>74.0</td>
    <td>56.0</td>
  </tr>
  <tr>
    <td>DE-PPN (d8d357 use_sent_span_encoder=False, use doc_sent_context in set_layers)</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
</tbody>
</table>

- Logs
  - DE-PPN (use_sent_span_encoder=False): [[Log]](Logs/shrink-deppn-reprod-1219-with_crf-ok_flag0-removeDup-noModEnc.log)

<h2 id="reference">💌 Reference</h2>

```bibtex
@inproceedings{yang-etal-2021-document,
    title = "Document-level Event Extraction via Parallel Prediction Networks",
    author = "Yang, Hang  and
      Sui, Dianbo  and
      Chen, Yubo  and
      Liu, Kang  and
      Zhao, Jun  and
      Wang, Taifeng",
    booktitle = "Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)",
    month = aug,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.acl-long.492",
    doi = "10.18653/v1/2021.acl-long.492",
    pages = "6298--6308",
}
```
