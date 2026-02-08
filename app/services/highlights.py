import librosa
import numpy as np


def detect_highlights(
    audio_path: str,
    clip_duration: int,
    clip_count: int
):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    total_duration = float(librosa.get_duration(y=y, sr=sr))

    # ---- HARD SAFETY GUARDS ----
    clip_duration = float(max(1.0, clip_duration))
    clip_count = int(max(1, clip_count))

    if total_duration <= clip_duration:
        # Video too short → return single safe clip
        return [(0.0, round(total_duration, 2))]

    window = 1.0
    hop = 0.5

    energies = []
    times = []

    t = 0.0
    while t + window < total_duration:
        segment = y[int(t * sr): int((t + window) * sr)]
        if len(segment) == 0:
            break
        rms = np.sqrt(np.mean(segment ** 2))
        energies.append(rms)
        times.append(t)
        t += hop

    if not energies:
        return [(0.0, min(clip_duration, total_duration))]

    energies = np.array(energies)
    times = np.array(times)

    # Normalize safely
    min_e, max_e = energies.min(), energies.max()
    if max_e > min_e:
        energies = (energies - min_e) / (max_e - min_e)
    else:
        energies = np.zeros_like(energies)

    # Pick extra candidates to reduce overlap loss
    candidates_needed = min(clip_count * 3, len(energies))
    top_idxs = np.argsort(energies)[-candidates_needed:]
    top_times = sorted(times[i] for i in top_idxs)

    raw_clips = []

    for t in top_times:
        start = max(0.0, t - clip_duration / 2)
        end = start + clip_duration

        # Clamp to duration
        if end > total_duration:
            end = total_duration
            start = max(0.0, end - clip_duration)

        start = round(start, 2)
        end = round(end, 2)

        if end - start >= 0.5:
            raw_clips.append((start, end))

    # ---- REMOVE OVERLAPS ----
    final_clips = []
    last_end = -1.0

    for start, end in sorted(raw_clips):
        if start >= last_end:
            final_clips.append((start, end))
            last_end = end
            if len(final_clips) >= clip_count:
                break

    # ---- FALLBACK: EVENLY SPACED ----
    if len(final_clips) < clip_count:
        needed = clip_count - len(final_clips)
        step = (total_duration - clip_duration) / (needed + 1)

        for i in range(needed):
            fs = step * (i + 1)
            fe = fs + clip_duration

            fs = round(max(0.0, fs), 2)
            fe = round(min(fe, total_duration), 2)

            if fe - fs < 0.5:
                continue

            overlaps = any(
                not (fe <= s or fs >= e)
                for s, e in final_clips
            )

            if not overlaps:
                final_clips.append((fs, fe))

    # ---- FINAL CLAMP & SORT ----
    cleaned = []
    for start, end in final_clips:
        start = max(0.0, round(start, 2))
        end = min(total_duration, round(end, 2))
        if end > start:
            cleaned.append((start, end))

    return sorted(cleaned)[:clip_count]
