import librosa
import numpy as np


def detect_highlights(
    audio_path: str,
    clip_duration: int,
    clip_count: int
):
    """
    Detect highlight segments based on audio energy
    """

    print("▶ Analysing audio for highlights...")

    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    window_sec = 1.0
    hop_sec = 0.5

    energies = []
    times = []

    t = 0.0
    while t + window_sec < duration:
        start = int(t * sr)
        end = int((t + window_sec) * sr)
        segment = y[start:end]

        if len(segment) == 0:
            break

        rms = np.sqrt(np.mean(segment ** 2))
        energies.append(rms)
        times.append(t)
        t += hop_sec

    energies = np.array(energies)
    times = np.array(times)

    highlights = []

    # 🎯 Energy-based detection
    if len(energies) > 0 and energies.max() > energies.mean() * 1.05:
        norm = (energies - energies.min()) / (energies.max() - energies.min() + 1e-8)
        top_idxs = np.argsort(norm)[-clip_count:]
        top_times = sorted(times[i] for i in top_idxs)

        for t in top_times:
            start = round(max(0, t - clip_duration / 2), 2)
            end = round(min(start + clip_duration, duration), 2)
            highlights.append((start, end))

    # 🧯 Fallback (guaranteed output)
    if not highlights:
        print("⚠ No strong peaks detected — using fallback.")
        step = duration / (clip_count + 1)
        for i in range(clip_count):
            s = round(i * step, 2)
            e = round(min(s + clip_duration, duration), 2)
            highlights.append((s, e))

    return highlights[:clip_count]
