<div align="center">
  <h1>Document-level Event Extraction via Parallel Prediction Networks</h1>
  <a href="#overview">🧱 Overview</a> | <a href="#datasets">💾 Datasets</a> | <a href="#dependencies">🌴 Dependencies</a> | <a href="#quickstart">🚀 QuickStart</a> | <a href="#implementation-detail">🔍 Implementation Details</a> | <a href="#results">📋 Results</a> | <a href="#reference">💌 Reference</a>
</div>


<h2 id="overview">🧱 Overview</h2>

Code for the paper ["Document-level Event Extraction via Parallel Prediction Networks"](https://aclanthology.org/2021.acl-long.492/).

This repo is built on the [official codes](https://github.com/HangYang-NLP/DE-PPN).
The official codes are not available to run due to some missing codes, and I can't wait to have a try, so I complete the missing part and create this repo.

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
$ nohup bash run.sh >deppn.log 2>&1 &
```

<h2 id="implementation-detail">🔍 Implementation Details</h2>

**Q:** How to construct the golden targets?
- In `DEEFeature.extract_predicted_instances`, records with **all** `None` arguments are labelled as `0` (NULL event).
- For arguments, the last entity (`role4None_embed`) represents `NULL` entity and is used as a role placeholder.

**Q:** How to select the best checkpoint?
- I follow the Doc2EDAG and use the MicroF1 on development set as the best model selection criteria.


<h2 id="results">📋 Results</h2>

Still running ...

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
