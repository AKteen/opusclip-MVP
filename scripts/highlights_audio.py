import librosa
import numpy as np

AUDIO_PATH = "output/audio.wav"

TARGET_SR = 16000
WINDOW_SEC = 1.0
HOP_SEC = 0.5
MIN_HIGHLIGHT_SEC = 20
FALLBACK_CLIP_SEC = 40


def get_highlights():
    print("▶ Analysing audio for highlights...")

    y, sr = librosa.load(AUDIO_PATH, sr=TARGET_SR, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    energies = []
    times = []

    t = 0.0
    while t + WINDOW_SEC < duration:
        start = int(t * sr)
        end = int((t + WINDOW_SEC) * sr)
        window = y[start:end]

        if len(window) == 0:
            break

        rms = np.sqrt(np.mean(window ** 2))
        energies.append(rms)
        times.append(t)
        t += HOP_SEC

    energies = np.array(energies)
    times = np.array(times)

    highlights = []

    # Energy based detection
    if len(energies) > 0 and energies.max() > energies.mean() * 1.05:
        norm = (energies - energies.min()) / (energies.max() - energies.min() + 1e-8)
        top_idxs = np.argsort(norm)[-80:]
        top_times = np.sort(times[top_idxs])

        start = top_times[0]
        prev = top_times[0]

        for t in top_times[1:]:
            if t - prev <= 2.0:
                prev = t
            else:
                if prev - start >= MIN_HIGHLIGHT_SEC:
                    highlights.append((round(start, 2), round(prev, 2)))
                start = t
                prev = t

        if prev - start >= MIN_HIGHLIGHT_SEC:
            highlights.append((round(start, 2), round(prev, 2)))

    # Fallback (guaranteed output)
    if not highlights:
        print("⚠ No strong energy peaks detected — using fallback segmentation.")
        step = duration / 6
        for i in range(5):
            s = round(i * step, 2)
            e = round(min(s + FALLBACK_CLIP_SEC, duration), 2)
            highlights.append((s, e))

    return highlights[:5]


if __name__ == "__main__":
    hs = get_highlights()
    print("Detected highlight segments:")
    for i, (s, e) in enumerate(hs, 1):
        print(f"{i}. {s}s → {e}s")
