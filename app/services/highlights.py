import librosa
import numpy as np

def detect_highlights(
    audio_path: str,
    clip_duration: int,
    clip_count: int
):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    window = 1.0
    hop = 0.5

    energies = []
    times = []

    t = 0.0
    while t + window < duration:
        segment = y[int(t*sr):int((t+window)*sr)]
        rms = np.sqrt(np.mean(segment**2))
        energies.append(rms)
        times.append(t)
        t += hop

    energies = np.array(energies)
    times = np.array(times)

    # Normalize
    energies = (energies - energies.min()) / (energies.max() - energies.min() + 1e-8)

    # Pick top energetic moments
    top_idxs = np.argsort(energies)[-clip_count:]
    top_times = sorted(times[i] for i in top_idxs)

    clips = []
    for t in top_times:
        start = round(max(0, t - clip_duration / 2), 2)
        end = round(min(start + clip_duration, duration), 2)
        clips.append((start, end))

    # Remove overlapping clips
    final_clips = []
    last_end = -1

    for start, end in sorted(clips):
        if start >= last_end:
            final_clips.append((start, end))
            last_end = end

    return final_clips[:clip_count]
