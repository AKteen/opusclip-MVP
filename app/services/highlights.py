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

    # Pick more candidates to account for overlaps
    candidates_needed = min(clip_count * 3, len(energies))
    top_idxs = np.argsort(energies)[-candidates_needed:]
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
            if len(final_clips) >= clip_count:
                break

    # Fallback: if still not enough clips, add evenly spaced ones
    if len(final_clips) < clip_count:
        missing = clip_count - len(final_clips)
        step = duration / (missing + 1)
        
        for i in range(missing):
            fallback_start = round(step * (i + 1), 2)
            fallback_end = round(min(fallback_start + clip_duration, duration), 2)
            
            # Check if this fallback clip overlaps with existing clips
            overlaps = any(not (fallback_end <= existing[0] or fallback_start >= existing[1]) 
                          for existing in final_clips)
            
            if not overlaps:
                final_clips.append((fallback_start, fallback_end))

    return final_clips[:clip_count]
