[![Mailing list : test](http://img.shields.io/badge/Email-gray.svg?style=for-the-badge&logo=gmail)](mailto:hello@silero.ai) [![Mailing list : test](http://img.shields.io/badge/Telegram-blue.svg?style=for-the-badge&logo=telegram)](https://t.me/joinchat/Bv9tjhpdXTI22OUgpOIIDg) [![License: CC BY-NC 4.0](https://img.shields.io/badge/License-MIT-lightgrey.svg?style=for-the-badge)](https://github.com/snakers4/silero-vad/blob/master/LICENSE) 
 
[![Open on Torch Hub](https://img.shields.io/badge/Torch-Hub-red?logo=pytorch&style=for-the-badge)](https://pytorch.org/hub/snakers4_silero-vad/) (coming soon)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/snakers4/silero-vad/blob/master/silero-vad.ipynb)

![header](https://user-images.githubusercontent.com/12515440/89997349-b3523080-dc94-11ea-9906-ca2e8bc50535.png)

- [Silero VAD](#silero-vad)
  - [Getting Started](#getting-started)
    - [PyTorch](#pytorch)
    - [ONNX](#onnx)
  - [Metrics](#metrics)
    - [Performance Metrics](#performance-metrics)
    - [VAD Quality Metrics](#vad-quality-metrics)
  - [FAQ](#faq)
    - [How VAD Works](#how-vad-works)
    - [VAD Quality Metrics Methodology](#vad-quality-metrics-methodology)
    - [How Number Detector Works](#how-number-detector-works)
    - [How Language Classifier Works](#how-language-classifier-works)
  - [Contact](#contact)
    - [Get in Touch](#get-in-touch)
    - [Commercial Inquiries](#commercial-inquiries)


# Silero VAD

![image](https://user-images.githubusercontent.com/36505480/102872739-ce099280-4448-11eb-967b-724440165eb5.png)

**Silero VAD: pre-trained enterprise-grade Voice Activity Detector (VAD), Number Detector and Language Classifier.**
Enterprise-grade Speech Products made refreshingly simple (see our [STT](https://github.com/snakers4/silero-models) models).

Currently, there are hardly any high quality / modern / free / public voice activity detectors except for WebRTC Voice Activity Detector ([link](https://github.com/wiseman/py-webrtcvad)). WebRTC though starts to show its age and it suffers from many false positives.

Also in some cases it is crucial to be able to anonymize large-scale spoken corpora (i.e. remove personal data). Typically personal data is considered to be private / sensitive if it contains (i) a name (ii) some private ID. Name recognition is a highly subjective matter and it depends on locale and business case, but Voice Activity and Number Detection are quite general tasks.

**Key features:**

- Modern, portable;
- Low memory footprint;
- Superior metrics to WebRTC;
- Trained on huge spoken corpora and noise / sound libraries;
- Slower than WebRTC, but fast enough for IOT / edge / mobile applications;
- Unlike WebRTC (which mostly tells silence from voice), our VAD can tell voice from noise / music / silence;

**Typical use cases:**

- Spoken corpora anonymization;
- Can be used together with WebRTC;
- Voice activity detection for IOT / edge / mobile use cases;
- Data cleaning and preparation, number and voice detection in general;
- PyTorch and ONNX can be used with a wide variety of deployment options and backends in mind; 

## Getting Started

The models are small enough to be included directly into this repository. Newer models will supersede older models directly.

Currently we provide the following functionality:

| PyTorch           | ONNX               | VAD                 | Number Detector    | Language Clf | Languages              | Colab |
|-------------------|--------------------|---------------------|--------------------|--------------|------------------------|-------| 
| :heavy_check_mark:| :heavy_check_mark: | :heavy_check_mark:  | :heavy_check_mark: |              | `ru`, `en`, `de`, `es` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/snakers4/silero-vad/blob/master/silero-vad.ipynb) |

**Version history:**

| Version | Date        | Comment                                           |
|---------|-------------|---------------------------------------------------|
| `v1`    | 2020-12-15  | Initial release                                               |
| `v1.1`  | 2020-12-24  | better vad models compatible with chunks shorter than 250 ms
| `v1.2`  | 2020-12-30  | Number Detector added
| `v2`    | coming soon | Add Language Classifier heads |

### PyTorch

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/snakers4/silero-vad/blob/master/silero-vad.ipynb)

[![Open on Torch Hub](https://img.shields.io/badge/Torch-Hub-red?logo=pytorch&style=for-the-badge)](https://pytorch.org/hub/snakers4_silero-vad/) (coming soon)

#### VAD

```python
import torch
torch.set_num_threads(1)
from pprint import pprint

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=True)

(get_speech_ts,
 _, read_audio,
 _, _, _) = utils

files_dir = torch.hub.get_dir() + '/snakers4_silero-vad_master/files'

wav = read_audio(f'{files_dir}/en.wav')
# full audio
# get speech timestamps from full audio file
speech_timestamps = get_speech_ts(wav, model,
                                  num_steps=4)
pprint(speech_timestamps)
```

#### Number Detector

```python
import torch
torch.set_num_threads(1)
from pprint import pprint

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_number_detector',
                              force_reload=True)

(get_number_ts,
 _, read_audio,
 _, _) = utils

files_dir = torch.hub.get_dir() + '/snakers4_silero-vad_master/files'

wav = read_audio(f'{files_dir}/en_num.wav')
# full audio
# get number timestamps from full audio file
number_timestamps = get_number_ts(wav, model)

pprint(number_timestamps)
```

### ONNX

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/snakers4/silero-vad/blob/master/silero-vad.ipynb)

You can run our models everywhere, where you can import the ONNX model or run ONNX runtime.

#### VAD

```python
import torch
import onnxruntime
from pprint import pprint

_, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=True)

(get_speech_ts,
 _, read_audio,
 _, _, _) = utils

files_dir = torch.hub.get_dir() + '/snakers4_silero-vad_master/files'

def init_onnx_model(model_path: str):
    return onnxruntime.InferenceSession(model_path)

def validate_onnx(model, inputs):
    with torch.no_grad():
        ort_inputs = {'input': inputs.cpu().numpy()}
        outs = model.run(None, ort_inputs)
        outs = [torch.Tensor(x) for x in outs]
    return outs
    
model = init_onnx_model(f'{files_dir}/model.onnx')
wav = read_audio(f'{files_dir}/en.wav')

# get speech timestamps from full audio file
speech_timestamps = get_speech_ts(wav, model, num_steps=4, run_function=validate_onnx) 
pprint(speech_timestamps)
```

#### Number Detector

```python
import torch
import onnxruntime
from pprint import pprint

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_number_detector',
                              force_reload=True)

(get_number_ts,
 _, read_audio,
 _, _) = utils

files_dir = torch.hub.get_dir() + '/snakers4_silero-vad_master/files'

def init_onnx_model(model_path: str):
    return onnxruntime.InferenceSession(model_path)

def validate_onnx(model, inputs):
    with torch.no_grad():
        ort_inputs = {'input': inputs.cpu().numpy()}
        outs = model.run(None, ort_inputs)
        outs = [torch.Tensor(x) for x in outs]
    return outs
    
model = init_onnx_model(f'{files_dir}/number_detector.onnx')
wav = read_audio(f'{files_dir}/en_num.wav')

# get speech timestamps from full audio file
number_timestamps = get_number_ts(wav, model, run_function=validate_onnx) 
pprint(number_timestamps)
```
## Metrics

### Performance Metrics

All speed test were run on AMD Ryzen Threadripper 3960X using only 1 thread: 
```
torch.set_num_threads(1) # pytorch
ort_session.intra_op_num_threads = 1 # onnx
ort_session.inter_op_num_threads = 1 # onnx
```

#### Streaming Latency

Streaming latency depends on 2 variables:

- **num_steps** - number of windows to split each audio chunk into. Our post-processing class keeps previous chunk in memory (250 ms), so new chunk (also 250 ms) is appended to it. The resulting big chunk (500 ms) is split into **num_steps** overlapping windows, each 250 ms long.

- **number of audio streams**

So **batch size** for streaming is **num_steps * number of audio streams**. Time between receiving new audio chunks and getting results is shown in picture:

| Batch size | Pytorch model time, ms | Onnx model time, ms |
| :-------------: |:-------------:| :-----:|
|     **2**      |          9             |        2            |
|     **4**      |          11            |        4            |
|     **8**      |          14            |        7            |
|     **16**     |          19            |        12           |
|     **40**     |          36            |        29           |
|     **80**     |          64            |        55           |
|     **120**    |          96            |        85           |
|     **200**    |          157           |        137          |

#### Full Audio Throughput

**RTS** (seconds of audio processed per second, real time speed, or 1 / RTF) for full audio processing depends on **num_steps** (see previous paragraph) and **batch size** (bigger is better).

| Batch size | num_steps | Pytorch model RTS      | Onnx model RTS      |
| :-------------: |:-------: | :-------------:| :-----:|
|     **40**  | **4**     |         68            |        86           |
|     **40**  | **8**     |         34            |        43           |
|     **80**  | **4**     |         78            |        91           |
|     **80**  | **8**     |         39            |        45           |
|    **120**  | **4**     |         78            |        88           |
|    **120**  | **8**     |         39            |        44           |
|    **200**  | **4**     |         80            |        91           |
|    **200**  | **8**     |         40            |        46           |

### VAD Quality Metrics

We use random 250 ms audio chunks for validation. Speech to non-speech ratio among chunks is about ~50/50 (i.e. balanced). Speech chunks are sampled from real audios in four different languages (English, Russian, Spanish, German), then random background noise is added to some of them (~40%). 

Since our VAD (only VAD, other networks are more flexible) was trained on chunks of the same length, model's output is just one float from 0 to 1 - **speech probability**. We use speech probabilities as thresholds for precision-recall curve. This can be extended to 100 - 150 ms (coming soon). Less than 100 - 150 ms cannot be distinguished as speech with confidence.

[Webrtc](https://github.com/wiseman/py-webrtcvad) splits audio into frames, each frame has corresponding number (0 **or** 1). We use 30ms frames for webrtc, so each 250 ms chunk is split into 8 frames, their **mean** value is used as a treshold for plot.

![image](https://user-images.githubusercontent.com/36505480/102872739-ce099280-4448-11eb-967b-724440165eb5.png)

## FAQ

### VAD Parameter Fine Tuning

- Among others, we provide several [utils](https://github.com/snakers4/silero-vad/blob/8b28767292b424e3e505c55f15cd3c4b91e4804b/utils.py#L52-L59) to simplify working with VAD;
- We provide sensible basic hyper-parameters that work for us, but your case can be different;
- `trig_sum` - overlapping windows are used for each audio chunk, trig sum defines average probability among those windows for switching into triggered state (speech state);
- `neg_trig_sum` - same as `trig_sum`, but for switching from triggered to non-triggered state (non-speech)
- `num_steps` - nubmer of overlapping windows to split audio chunk into (we recommend 4 or 8)
- `num_samples_per_window` - number of samples in each window, our models were trained using `4000` samples (250 ms) per window, so this is preferable value (lesser values reduce [quality](https://github.com/snakers4/silero-vad/issues/2#issuecomment-750840434));

### How VAD Works

- Audio is split into 250 ms chunks (you can choose any chunk size, but quality with chunks shorter than 100ms will suffer and there will be more false positives and "unnatural" pauses);
- VAD keeps record of a previous chunk (or zeros at the beginning of the stream);
- Then this 500 ms audio (250 ms + 250 ms) is split into N (typically 4 or 8) windows and the model is applied to this window batch. Each window is 250 ms long (naturally, windows overlap);
- Then probability is averaged across these windows;
- Though typically pauses in speech are 300 ms+ or longer (pauses less than 200-300ms are typically not meaninful), it is hard to confidently classify speech vs noise / music on very short chunks (i.e. 30 - 50ms);
- ~~We are working on lifting this limitation, so that you can use 100 - 125ms windows~~;

### VAD Quality Metrics Methodology

Please see [Quality Metrics](#quality-metrics)

### How Number Detector Works

- It is recommended to split long audio into short ones (< 15s) and apply model on each of them;
- Number Detector can classify if whole audio contains a number, or if each audio frame contains a number;
- Audio is splitted into frames in a certain way, so, having a per-frame output, we can restore timing bounds for a numbers with an accuracy of about 0.2s;

### How Language Classifier Works

TBD, but there is no explicit limiation on the way audio is split into chunks.

## Contact

### Get in Touch

Try our models, create an [issue](https://github.com/snakers4/silero-vad/issues/new), start a [discussion](https://github.com/snakers4/silero-vad/discussions/new), join our telegram [chat](https://t.me/joinchat/Bv9tjhpdXTI22OUgpOIIDg), [email](mailto:hello@silero.ai) us.

### Commercial Inquiries

Please see our [wiki](https://github.com/snakers4/silero-models/wiki) and [tiers](https://github.com/snakers4/silero-models/wiki/Licensing-and-Tiers) for relevant information and [email](mailto:hello@silero.ai) us directly.
