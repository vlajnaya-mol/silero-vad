import torch
import torchaudio
from typing import List
from itertools import repeat
from collections import deque
import torch.nn.functional as F


torchaudio.set_audio_backend("soundfile")  # switch backend


def validate(model,
             inputs: torch.Tensor):
    with torch.no_grad():
        outs = model(inputs)
    return outs


def read_audio(path: str,
               target_sr: int = 16000):

    assert torchaudio.get_audio_backend() == 'soundfile'
    wav, sr = torchaudio.load(path)

    if wav.size(0) > 1:
        wav = wav.mean(dim=0, keepdim=True)

    if sr != target_sr:
        transform = torchaudio.transforms.Resample(orig_freq=sr,
                                                   new_freq=target_sr)
        wav = transform(wav)
        sr = target_sr

    assert sr == target_sr
    return wav.squeeze(0)


def save_audio(path: str,
               tensor: torch.Tensor,
               sr: int = 16000):
    torchaudio.save(path, tensor, sr)


def init_jit_model(model_path: str,
                   device=torch.device('cpu')):
    torch.set_grad_enabled(False)
    model = torch.jit.load(model_path, map_location=device)
    model.eval()
    return model


def get_speech_ts(wav: torch.Tensor,
                  model,
                  trig_sum: float = 0.25,
                  neg_trig_sum: float = 0.07,
                  num_steps: int = 8,
                  batch_size: int = 200,
                  num_samples_per_window: int = 4000,
                  run_function=validate):

    num_samples = num_samples_per_window
    assert num_samples % num_steps == 0
    step = int(num_samples / num_steps)  # stride / hop
    outs = []
    to_concat = []

    for i in range(0, len(wav), step):
        chunk = wav[i: i+num_samples]
        if len(chunk) < num_samples:
            chunk = F.pad(chunk, (0, num_samples - len(chunk)))
        to_concat.append(chunk.unsqueeze(0))
        if len(to_concat) >= batch_size:
            chunks = torch.Tensor(torch.cat(to_concat, dim=0))
            out = run_function(model, chunks)
            outs.append(out)
            to_concat = []

    if to_concat:
        chunks = torch.Tensor(torch.cat(to_concat, dim=0))
        out = run_function(model, chunks)
        outs.append(out)

    outs = torch.cat(outs, dim=0)

    buffer = deque(maxlen=num_steps)  # maxlen reached => first element dropped
    triggered = False
    speeches = []
    current_speech = {}

    speech_probs = outs[:, 1]  # this is very misleading
    for i, predict in enumerate(speech_probs):  # add name
        buffer.append(predict)
        if ((sum(buffer) / len(buffer))>= trig_sum) and not triggered:
            triggered = True
            current_speech['start'] = step * max(0, i-num_steps)
        if ((sum(buffer) / len(buffer)) < neg_trig_sum) and triggered:
            current_speech['end'] = step * i
            if (current_speech['end'] - current_speech['start']) > 10000:
                speeches.append(current_speech)
            current_speech = {}
            triggered = False
    if current_speech:
        current_speech['end'] = len(wav)
        speeches.append(current_speech)
    return speeches


def get_number_ts(wav: torch.Tensor,
                  model,
                  model_stride=8,
                  hop_length=160,
                  sample_rate=16000,
                  run_function=validate):
    wav = torch.unsqueeze(wav, dim=0)
    perframe_logits = run_function(model, wav)[0]
    perframe_preds = torch.argmax(torch.softmax(perframe_logits, dim=1), dim=1).squeeze()   # (1, num_frames_strided)
    extended_preds = []
    for i in perframe_preds:
        extended_preds.extend([i.item()] * model_stride)
    # len(extended_preds) is *num_frames_real*; for each frame of audio we know if it has a number in it.
    triggered = False
    timings = []
    cur_timing = {}
    for i, pred in enumerate(extended_preds):
        if pred == 1:
            if not triggered:
                cur_timing['start'] = int((i * hop_length) / (sample_rate / 1000))
                triggered = True
        elif pred == 0:
            if triggered:
                cur_timing['end'] = int((i * hop_length) / (sample_rate / 1000))
                timings.append(cur_timing)
                cur_timing = {}
                triggered = False
    if cur_timing:
        cur_timing['end'] = int(len(wav) / (sample_rate / 1000))
        timings.append(cur_timing)
    return timings


class VADiterator:
    def __init__(self,
                 trig_sum: float = 0.26,
                 neg_trig_sum: float = 0.07,
                 num_steps: int = 8,
                 num_samples_per_window: int = 4000):
        self.num_samples = num_samples_per_window
        self.num_steps = num_steps
        assert self.num_samples % num_steps == 0
        self.step = int(self.num_samples / num_steps)   # 500 samples is good enough
        self.prev = torch.zeros(self.num_samples)
        self.last = False
        self.triggered = False
        self.buffer = deque(maxlen=num_steps)
        self.num_frames = 0
        self.trig_sum = trig_sum
        self.neg_trig_sum = neg_trig_sum
        self.current_name = ''

    def refresh(self):
        self.prev = torch.zeros(self.num_samples)
        self.last = False
        self.triggered = False
        self.buffer = deque(maxlen=self.num_steps)
        self.num_frames = 0

    def prepare_batch(self, wav_chunk, name=None):
        if (name is not None) and (name != self.current_name):
            self.refresh()
            self.current_name = name
        assert len(wav_chunk) <= self.num_samples
        self.num_frames += len(wav_chunk)
        if len(wav_chunk) < self.num_samples:
            wav_chunk = F.pad(wav_chunk, (0, self.num_samples - len(wav_chunk)))  # short chunk => eof audio
            self.last = True

        stacked = torch.cat([self.prev, wav_chunk])
        self.prev = wav_chunk

        overlap_chunks = [stacked[i:i+self.num_samples].unsqueeze(0)
                          for i in range(self.step, self.num_samples+1, self.step)]
        return torch.cat(overlap_chunks, dim=0)

    def state(self, model_out):
        current_speech = {}
        speech_probs = model_out[:, 1]  # this is very misleading
        for i, predict in enumerate(speech_probs):
            self.buffer.append(predict)
            if ((sum(self.buffer) / len(self.buffer)) >= self.trig_sum) and not self.triggered:
                self.triggered = True
                current_speech[self.num_frames - (self.num_steps-i) * self.step] = 'start'
            if ((sum(self.buffer) / len(self.buffer)) < self.neg_trig_sum) and self.triggered:
                current_speech[self.num_frames - (self.num_steps-i) * self.step] = 'end'
                self.triggered = False
        if self.triggered and self.last:
            current_speech[self.num_frames] = 'end'
        if self.last:
            self.refresh()
        return current_speech, self.current_name


def state_generator(model,
                    audios: List[str],
                    onnx: bool = False,
                    trig_sum: float = 0.26,
                    neg_trig_sum: float = 0.07,
                    num_steps: int = 8,
                    num_samples_per_window: int = 4000,
                    audios_in_stream: int = 2,
                    run_function=validate):
    VADiters = [VADiterator(trig_sum, neg_trig_sum, num_steps, num_samples_per_window) for i in range(audios_in_stream)]
    for i, current_pieces in enumerate(stream_imitator(audios, audios_in_stream, num_samples_per_window)):
        for_batch = [x.prepare_batch(*y) for x, y in zip(VADiters, current_pieces)]
        batch = torch.cat(for_batch)

        outs = run_function(model, batch)
        vad_outs = torch.split(outs, num_steps)

        states = []
        for x, y in zip(VADiters, vad_outs):
            cur_st = x.state(y)
            if cur_st[0]:
                states.append(cur_st)
        yield states


def stream_imitator(audios: List[str],
                    audios_in_stream: int,
                    num_samples_per_window: int = 4000):
    audio_iter = iter(audios)
    iterators = []
    num_samples = num_samples_per_window
    # initial wavs
    for i in range(audios_in_stream):
        next_wav = next(audio_iter)
        wav = read_audio(next_wav)
        wav_chunks = iter([(wav[i:i+num_samples], next_wav) for i in range(0, len(wav), num_samples)])
        iterators.append(wav_chunks)
    print('Done initial Loading')
    good_iters = audios_in_stream
    while True:
        values = []
        for i, it in enumerate(iterators):
            try:
                out, wav_name = next(it)
            except StopIteration:
                try:
                    next_wav = next(audio_iter)
                    print('Loading next wav: ', next_wav)
                    wav = read_audio(next_wav)
                    iterators[i] = iter([(wav[i:i+num_samples], next_wav) for i in range(0, len(wav), num_samples)])
                    out, wav_name = next(iterators[i])
                except StopIteration:
                    good_iters -= 1
                    iterators[i] = repeat((torch.zeros(num_samples), 'junk'))
                    out, wav_name = next(iterators[i])
                    if good_iters == 0:
                        return
            values.append((out, wav_name))
        yield values


def single_audio_stream(model,
                        audio: str,
                        onnx: bool = False,
                        trig_sum: float = 0.26,
                        neg_trig_sum: float = 0.07,
                        num_steps: int = 8,
                        num_samples_per_window: int = 4000,
                        run_function=validate):
    num_samples = num_samples_per_window
    VADiter = VADiterator(trig_sum, neg_trig_sum, num_steps, num_samples_per_window)
    wav = read_audio(audio)
    wav_chunks = iter([wav[i:i+num_samples] for i in range(0, len(wav), num_samples)])
    for chunk in wav_chunks:
        batch = VADiter.prepare_batch(chunk)

        outs = run_function(model, batch)
        vad_outs = outs  # this is very misleading

        states = []
        state = VADiter.state(vad_outs)
        if state[0]:
            states.append(state[0])
        yield states


def collect_chunks(tss: List[dict],
                   wav: torch.Tensor):
    chunks = []
    for i in tss:
        chunks.append(wav[i['start']: i['end']])
    return torch.cat(chunks)


def drop_chunks(tss: List[dict],
                wav: torch.Tensor):
    chunks = []
    cur_start = 0
    for i in tss:
        chunks.append((wav[cur_start: i['start']]))
        cur_start = i['end']
    return torch.cat(chunks)
