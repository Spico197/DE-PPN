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

I've sync the codes with the latest official remote (f920cd67ec0eb1d8386d3231c97371c3e11f0387), and here are the results.

The results of `Doc2EDAG` is from the original paper, and the results of `DE-PPN` is our reproduced results.

- Speed

| Model  | Train (min/epoch) | Inference (docs/s) | Total Training Process (hours) |
| :----- | ----------------: | -----------------: | -----------------------------: |
| DE-PPN |             52.9  |               3.1  |                          94.5  |

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
    <td>DE-PPN</td>
    <td>36.3</td>
    <td>38.1</td>
    <td>37.2</td>
    <td>34.0</td>
    <td>50.9</td>
    <td>40.8</td>
    <td>34.6</td>
    <td>43.2</td>
    <td>38.4</td>
    <td>32.0</td>
    <td>39.8</td>
    <td>35.5</td>
    <td>44.5</td>
    <td>38.9</td>
    <td>41.5</td>
    <td>36.3</td>
    <td>42.2</td>
    <td>38.7</td>
    <td>38.8</td>
    <td>42.0</td>
    <td>40.4</td>
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
    <td>DE-PPN</td>
    <td>36.3</td>
    <td>38.4</td>
    <td>40.1</td>
    <td>48.5</td>
    <td>38.1</td>
    <td>39.1</td>
    <td>37.3</td>
    <td>31.4</td>
    <td>40.3</td>
    <td>42.7</td>
    <td>38.4</td>
    <td>40.0</td>
    <td>39.6</td>
    <td>41.7</td>
  </tr>
</tbody>
</table>

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
