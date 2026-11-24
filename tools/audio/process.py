"""Audio agent: raw Higgsfield mp3 -> game-ready wav/ogg + game/assets/audio/audio.json.

python3 tools/audio/process.py           (from the repo root; work/audio/process.py is the first-pass copy)
Writes game/assets/audio/sfx/<name>.wav, game/assets/audio/music/<name>.ogg, game/assets/audio/audio.json and
work/audio/processed.json (numbers for docs/notes/audio.md).
"""
import json, os, subprocess, sys, wave
import numpy as np

SR = 44100
RAW = 'art_src/audio/raw'
OUT_SFX = 'game/assets/audio/sfx'
OUT_MUS = 'game/assets/audio/music'
FFMPEG4 = '/opt/homebrew/opt/ffmpeg@4/bin/ffmpeg'
PEAK = 10 ** (-3 / 20)          # one-shots and loops normalised to -3 dBFS sample peak
MUSIC_LUFS = -16.0
MUSIC_VOL = -5.0                 # music sits under the effects (manifest volume_db)

# per-sound processing. hp/lp: filter Hz. onset_db: start where the 5 ms RMS first comes within this many dB of
# its peak. maxlen: useful part in seconds. decay: exp decay time constant shaped over the cut (makes a thud).
# target: loudness (max 400 ms RMS, dBFS) the manifest volume_db aims at; loops use the mean RMS instead.
# skip: ignore the first N seconds of the raw when looking for the onset (the generator put the real hit later).
# layer: dict(src=<mp3 path>, hp, lp, gain_db = layer peak relative to the base peak, delay s) summed onto the trimmed
#   one-shot, each trimmed to its own onset. Loops: region=(a, b) s of the raw, agc=True flattens a slow level drift,
#   layer=dict(src, hp, region, rms_rel_db = layer RMS relative to the base RMS) summed before the crossfade.
# Follow-up pass 2026-11-22: ten sounds regenerated (art_src/audio/raw; the first takes are in art_src/audio/raw_v1).
V1 = 'art_src/audio/raw_v1'
D = dict(hp=30, lp=None, onset_db=24, maxlen=None, tail_db=45, decay=None, fade=None, skip=0.0, layer=None)
CFG = {
	# player
	'sword_swing':  dict(hp=100, maxlen=0.45, target=-18, pr=0.06, cat='player'),
	# sword_hit: the regenerated take was worse (low rumble, thud at 0.60 s, bright crack 0.2 s later, cut off at the
	# file end); the first take is back in raw/ (slash at 0.54 s, then the thud), settings unchanged.
	'sword_hit':    dict(hp=80, onset_db=10, maxlen=0.45, target=-14, pr=0.05, cat='player'),
	# glance v2: knock at 0.02 s + a noisy scrape, no ring. Layered with the 3.4 kHz ring of the first take (HP 1500).
	'glance':       dict(hp=220, maxlen=0.45, layer=dict(src=f'{V1}/glance.mp3', hp=1500, gain_db=-6.0),
		target=-15, pr=0.06, cat='player'),
	'roll':         dict(hp=80, maxlen=0.7, target=-21, pr=0.05, cat='player'),
	'step_dirt':    dict(hp=80, maxlen=0.28, target=-27, pr=0.08, cat='step'),
	# step_stone v2: three steps (0.02, 0.64, 0.95 s); the 0.64 s one has the heel click, the last one is cut off.
	'step_stone':   dict(hp=110, skip=0.6, maxlen=0.16, target=-27, pr=0.08, cat='step'),
	'shield_up':    dict(hp=80, maxlen=0.7, target=-20, pr=0.04, cat='player'),
	'block':        dict(hp=60, maxlen=0.8, target=-14, pr=0.04, cat='player'),
	'reflect':      dict(hp=80, maxlen=1.6, target=-14, pr=0.0, cat='player'),
	'hurt':         dict(hp=90, maxlen=0.4, target=-16, pr=0.05, cat='player'),   # v2: clean grunt 0.02-0.30 s
	'death':        dict(hp=50, maxlen=2.0, target=-14, pr=0.0, cat='player'),
	'petrify':      dict(maxlen=1.6, target=-15, pr=0.0, cat='player'),
	# cyclops
	'cyclops_roar':       dict(target=-12, pr=0.0, cat='boss'),
	# v2: a real boom at 0.04 s, then more booms every ~0.2 s: a short decay keeps only the first (no low-pass needed)
	'cyclops_step':       dict(hp=35, maxlen=0.4, decay=0.09, target=-19, pr=0.06, cat='boss'),
	'cyclops_sweep_warn': dict(maxlen=0.7, target=-14, pr=0.0, cat='warn'),
	'cyclops_sweep':      dict(maxlen=0.6, target=-12, pr=0.03, cat='boss'),
	'cyclops_slam_warn':  dict(maxlen=1.5, target=-14, pr=0.0, cat='warn'),
	'cyclops_slam':       dict(maxlen=1.6, target=-10, pr=0.03, cat='boss'),
	'cyclops_stuck':      dict(target=-15, pr=0.0, cat='boss'),
	'cyclops_pull_free':  dict(maxlen=1.2, target=-14, pr=0.0, cat='boss'),
	'cyclops_hurt':       dict(maxlen=1.3, target=-12, pr=0.04, cat='boss'),
	'cyclops_death':      dict(target=-11, pr=0.0, cat='boss'),
	# medusa
	'medusa_hiss':            dict(fade=0.4, target=-17, pr=0.04, cat='boss'),
	'medusa_gaze_warn':       dict(maxlen=1.3, target=-14, pr=0.0, cat='warn'),
	'medusa_gaze':            dict(maxlen=1.4, fade=0.3, target=-12, pr=0.0, cat='boss'),
	'medusa_stun':            dict(maxlen=1.6, target=-12, pr=0.0, cat='boss'),
	'medusa_tail_swipe_warn': dict(maxlen=0.75, target=-14, pr=0.0, cat='warn'),
	'medusa_tail_swipe':      dict(maxlen=0.6, target=-12, pr=0.03, cat='boss'),
	'medusa_hurt':            dict(hp=60, maxlen=1.3, target=-12, pr=0.04, cat='boss'),
	'medusa_death':           dict(hp=50, target=-11, pr=0.0, cat='boss'),
	# hydra
	'hydra_roar':            dict(target=-11, pr=0.0, cat='boss'),
	'hydra_fire_sweep_warn': dict(hp=40, maxlen=1.6, fade=0.2, target=-14, pr=0.0, cat='warn'),   # v2: no gap, no splice
	'hydra_fire':            dict(loop=True, xfade=0.5, target=-14, cat='boss'),
	'hydra_head_down':       dict(maxlen=1.6, target=-13, pr=0.0, cat='boss'),
	'hydra_stomp_warn':      dict(onset_db=10, maxlen=0.9, target=-14, pr=0.0, cat='warn'),
	'hydra_stomp':           dict(maxlen=1.8, target=-10, pr=0.03, cat='boss'),
	'hydra_bite_warn':       dict(hp=60, maxlen=0.8, target=-14, pr=0.0, cat='warn'),
	# v2: hiss 0-0.36 s, a crack at 0.38 s, the jaw snap + crunch at 0.54 s: start on the snap
	'hydra_bite':            dict(hp=60, skip=0.5, onset_db=12, maxlen=0.4, target=-12, pr=0.04, cat='boss'),
	'hydra_hurt':            dict(maxlen=1.3, target=-12, pr=0.04, cat='boss'),
	'hydra_death':           dict(target=-11, pr=0.0, cat='boss'),
	# world
	'wing_flap':  dict(hp=60, maxlen=0.8, target=-20, pr=0.05, cat='world'),
	'neigh':      dict(hp=80, target=-16, pr=0.03, cat='world'),
	'mount':      dict(hp=60, maxlen=0.9, target=-18, pr=0.03, cat='world'),
	'land':       dict(hp=40, maxlen=1.0, target=-16, pr=0.03, cat='world'),
	'thunder':    dict(onset_db=12, maxlen=2.4, fade=0.5, target=-12, pr=0.0, cat='world'),
	'wind_loop':  dict(loop=True, xfade=0.8, target=-20, cat='amb'),
	'sea_loop':   dict(loop=True, xfade=0.8, target=-26, cat='amb'),
	'lava_loop':  dict(loop=True, xfade=0.8, target=-24, cat='amb'),
	# fire_loop v2: a loud low roar (84 % below 150 Hz, fades out after 3.0 s) with no crackle; v1 was sparse crackle
	# only. Roar 0.1-2.9 s (level drift flattened) + the v1 crackle (HP 1500) 10 dB under it, one crossfade.
	'fire_loop':  dict(hp=60, loop=True, xfade=0.5, region=(0.1, 2.9), agc=True,
		layer=dict(src=f'{V1}/fire_loop.mp3', hp=1500, region=(0.0, 2.8), rms_rel_db=-10.0), target=-22, cat='amb'),
	'beacon_loop': dict(hp=60, loop=True, xfade=0.6, target=-24, cat='amb'),
	# ui + stings
	'ui_move':    dict(hp=100, maxlen=0.3, target=-20, pr=0.03, cat='ui'),
	# ui_accept v2 is only a 60 ms 2.76 kHz bell ping (no chord): the ui_move chord stays, the ping is layered on it
	'ui_accept':  dict(synth='ui_chord', layer=dict(src=f'{RAW}/ui_accept.mp3', hp=1000, gain_db=0.0),
		target=-19, pr=0.0, cat='ui'),
	'ui_back':    dict(hp=60, maxlen=0.6, target=-20, pr=0.0, cat='ui'),
	'victory':    dict(fade=0.4, target=-12, pr=0.0, cat='sting'),
	'defeat':     dict(fade=0.4, target=-14, pr=0.0, cat='sting'),
	'title_card': dict(fade=0.3, target=-12, pr=0.0, cat='sting'),
	# trophy v2: chimes at 0.0 and 0.8 s (5.3 / 8.4 / 9.4 kHz) + a 1 s ring; HP 1500 drops the low hiss of the tail
	'trophy':     dict(hp=1500, fade=0.4, target=-16, pr=0.0, cat='sting'),
}
# bus + 3D settings per category: (bus, positional, unit_size, max_distance)
CAT = {
	'player': ('SFX', True, 6.0, 90.0), 'step': ('SFX', True, 4.0, 40.0), 'boss': ('SFX', True, 22.0, 260.0),
	'warn': ('SFX', True, 24.0, 260.0), 'world': ('SFX', True, 10.0, 160.0), 'amb': ('SFX', False, 6.0, 60.0),
	'ui': ('UI', False, 1.0, 1.0), 'sting': ('UI', False, 1.0, 1.0),
}
AMB_3D = {'fire_loop': (2.5, 28.0), 'beacon_loop': (18.0, 320.0),   # loops placed in the world when given a position
	'thunder': (90.0, 900.0)}                                             # bolts strike 50-130 m up, storm wall 400 m away


def decode(name, hp=None, lp=None, ch=1):
	af = []
	if hp:
		af.append(f'highpass=f={hp}:poles=2')
	if lp:
		af.append(f'lowpass=f={lp}:poles=2')
	src = name if name.endswith('.mp3') else f'{RAW}/{name}.mp3'
	cmd = ['ffmpeg', '-v', 'error', '-i', src]
	if af:
		cmd += ['-af', ','.join(af)]
	cmd += ['-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-']
	x = np.frombuffer(subprocess.check_output(cmd), np.float32).astype(np.float64)
	return x.reshape(-1, ch) if ch > 1 else x


def env_db(x, win=220):
	n = len(x) // win
	return 20 * np.log10(np.sqrt(np.mean(x[:n * win].reshape(n, win) ** 2, axis=1)) + 1e-9), win


def max_m(x):
	"""max 400 ms RMS (100 ms hop), dBFS."""
	w, h = int(0.4 * SR), int(0.1 * SR)
	if len(x) <= w:
		return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
	return max(20 * np.log10(np.sqrt(np.mean(x[i:i + w] ** 2)) + 1e-9) for i in range(0, len(x) - w, h))


def write_wav(path, x):
	x = np.clip(x, -1, 1)
	with wave.open(path, 'wb') as f:
		f.setnchannels(1 if x.ndim == 1 else x.shape[1])
		f.setsampwidth(2)
		f.setframerate(SR)
		f.writeframes((x * 32767).round().astype('<i2').tobytes())


def loopify(x, xfade_s):
	"""Equal-power crossfade of the tail into the head: y[0] continues y[-1] sample for sample."""
	c = int(xfade_s * SR)
	t = np.linspace(0, np.pi / 2, c, endpoint=False)
	fi, fo = np.sin(t), np.cos(t)
	if x.ndim > 1:
		fi, fo = fi[:, None], fo[:, None]
	y = x[:len(x) - c].copy()
	y[:c] = x[:c] * fi + x[len(x) - c:] * fo
	return y


def seam_check(y, off=0):
	"""Seam numbers: sample jump at the wrap (end -> loop offset) vs the 99th percentile step, and the RMS of 50 ms
	around the wrap vs the 10th-90th percentile of all 100 ms windows."""
	m = y if y.ndim == 1 else y.mean(axis=1)
	steps = np.abs(np.diff(m))
	jump = abs(m[off] - m[-1])
	w = int(0.05 * SR)
	ring = np.concatenate([m[-w:], m[off:off + w]])
	seam_rms = 20 * np.log10(np.sqrt(np.mean(ring ** 2)) + 1e-9)
	nb = [20 * np.log10(np.sqrt(np.mean(m[i:i + 2 * w] ** 2)) + 1e-9) for i in range(0, len(m) - 2 * w, w)]
	return dict(jump=round(float(jump), 5), median_step=round(float(np.median(steps)), 5),
		jump_ratio=round(float(jump / (np.percentile(steps, 99) + 1e-9)), 3),
		seam_rms_db=round(float(seam_rms), 1), rms_p10_p90=[round(float(np.percentile(nb, 10)), 1), round(float(np.percentile(nb, 90)), 1)])


def limit(x, ceil=PEAK, look=0.004, rel=0.08):
	"""Look-ahead peak limiter (gain reaches its minimum before each peak, smooth attack, exponential release)."""
	from numpy.lib.stride_tricks import sliding_window_view
	a = np.abs(x)
	w = int(look * SR)
	g = np.minimum(1.0, ceil / np.maximum(a, 1e-9))
	pad = np.concatenate([np.ones(w), g, np.ones(w)])
	gmin = sliding_window_view(pad, 2 * w + 1).min(axis=1)
	gmin = np.convolve(gmin, np.ones(w) / w, mode='same')
	gmin = np.minimum(gmin, sliding_window_view(np.concatenate([np.ones(w // 2), g, np.ones(w - w // 2)]), w + 1).min(axis=1)[:len(g)])
	out = np.empty_like(gmin)
	cur = 1.0
	k = 1 - np.exp(-1 / (rel * SR))
	for i, v in enumerate(gmin):
		cur = v if v < cur else cur + k * (v - cur)
		out[i] = cur
	return np.clip(x * out, -ceil, ceil)


def fade(x, fin, fout):
	x = x.copy()
	a, b = int(fin * SR), int(fout * SR)
	if a > 0:
		x[:a] *= np.linspace(0, 1, a)
	if b > 0:
		x[-b:] *= np.linspace(1, 0, b) ** 2
	return x


def zero_cross_before(x, i, look=200):
	j0 = max(1, i - look)
	seg = x[j0:i + 1]
	z = np.where(np.signbit(seg[:-1]) != np.signbit(seg[1:]))[0]
	return j0 + int(z[-1]) + 1 if len(z) else i


def synth_ui_chord():
	"""ui_accept: the raw file is a 294 Hz hum. Stand-in: the ui_move lyre pluck stacked as a rising triad (root, +4, +7
	semitones, 35 ms apart) = a short bright chord, until the lead regenerates it."""
	base = decode('ui_move', hp=100)
	e, win = env_db(base)
	on = int(np.argmax(e > e.max() - 24)) * win
	base = base[on:on + int(0.45 * SR)]
	out = np.zeros(int(0.6 * SR))
	for k, (semi, gain) in enumerate([(0, 1.0), (4, 0.8), (7, 0.75), (12, 0.35)]):
		r = 2 ** (semi / 12)
		idx = np.arange(0, len(base) - 1, r)
		v = np.interp(idx, np.arange(len(base)), base) * gain
		d = int(0.035 * k * SR)
		n = min(len(v), len(out) - d)
		out[d:d + n] += v[:n]
	return out


def onset_at(x, onset_db, skip=0.0):
	"""Sample index where the 5 ms RMS first comes within onset_db of its peak (after `skip` s), 3 ms earlier, on a
	zero crossing."""
	e, win = env_db(x)
	s = min(int(skip * SR) // win, len(e) - 1)
	pk = e[s:].max()
	on_i = (s + int(np.argmax(e[s:] > pk - onset_db))) * win
	return zero_cross_before(x, max(0, on_i - int(0.003 * SR)))


def flatten_level(x, win_s=0.4, lo=0.5, hi=2.0):
	"""Slow gain riding: divide by a smoothed 400 ms RMS envelope (gain clipped to [lo, hi]) so a drifting take
	becomes an even bed. Short events (crackles) keep their shape."""
	h = int(0.01 * SR)
	n = len(x) // h
	r = np.sqrt(np.mean(x[:n * h].reshape(n, h) ** 2, axis=1)) + 1e-9
	k = max(1, int(win_s / 0.01))
	r = np.sqrt(np.convolve(r ** 2, np.ones(k) / k, mode='same'))
	g = np.clip(np.median(r) / r, lo, hi)
	g = np.convolve(np.concatenate([np.full(k, g[0]), g, np.full(k, g[-1])]), np.ones(k) / k, mode='same')[k:-k]
	gs = np.interp(np.arange(len(x)), np.arange(n) * h + h / 2, g)
	return x * gs


def rms(x):
	return float(np.sqrt(np.mean(x ** 2)) + 1e-12)


def process_sfx(name, c):
	if c.get('synth') == 'ui_chord':
		x = synth_ui_chord()
	else:
		x = decode(name, c['hp'], c['lp'])
	raw_len = len(x) / SR
	info = {}
	if c.get('loop'):
		if c.get('region'):
			a, b = c['region']
			x = x[int(a * SR):int(b * SR)]
		if c.get('agc'):
			x = flatten_level(x)
		L = c.get('layer')
		if L:
			z = decode(L['src'], L.get('hp'), L.get('lp'))
			if L.get('region'):
				z = z[int(L['region'][0] * SR):int(L['region'][1] * SR)]
			z = np.resize(z, len(x)) if len(z) < len(x) else z[:len(x)]
			z = z * (rms(x) * 10 ** (L['rms_rel_db'] / 20) / rms(z))
			x = x + z
			info['layer'] = dict(src=L['src'], rms_rel_db=L['rms_rel_db'])
		y = loopify(x, c['xfade'])
		y = y * (PEAK / np.abs(y).max())
		need = c['target'] - 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)
		if need > 3.0:
			drive = min(need - 2.0, 10.0)
			# limit a doubled copy so the wrap stays continuous (the limiter state runs across the seam), keep the 2nd half
			yy = limit(np.concatenate([y, y]) * 10 ** (drive / 20))
			y = yy[len(y):]
			info['limiter_drive_db'] = round(drive, 1)
		info['seam'] = seam_check(y)
		level = 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)
	else:
		if c.get('splice_gap'):
			e, win = env_db(x)
			quiet = e < e.max() - 45
			# longest quiet run after the first 0.2 s
			best, cur, start = (0, 0, 0), 0, 0
			for i, q in enumerate(quiet):
				if q and i * win > 0.2 * SR:
					if cur == 0:
						start = i
					cur += 1
					if cur > best[0]:
						best = (cur, start, i)
				else:
					cur = 0
			if best[0] * win > 0.15 * SR:
				a, b = best[1] * win, (best[2] + 1) * win
				xf = int(0.04 * SR)
				head, tail = x[:a + xf].copy(), x[b - xf:].copy()
				t = np.linspace(0, np.pi / 2, xf)
				head[-xf:] = head[-xf:] * np.cos(t) + tail[:xf] * np.sin(t)
				x = np.concatenate([head, tail[xf:]])
				info['spliced_out'] = [round(a / SR, 3), round(b / SR, 3)]
		e, win = env_db(x)
		pk = e.max()
		on_i = onset_at(x, c['onset_db'], c['skip'])
		above = np.where(e > pk - c['tail_db'])[0]
		end_i = min(len(x), (int(above[-1]) + 1) * win)
		if c['maxlen']:
			end_i = min(end_i, on_i + int(c['maxlen'] * SR))
		y = x[on_i:end_i]
		if c['decay']:
			tt = np.arange(len(y)) / SR
			y = y * np.exp(-np.maximum(tt - 0.03, 0) / c['decay'])
		L = c['layer']
		if L:
			z = decode(L['src'], L.get('hp'), L.get('lp'))
			z = z[onset_at(z, L.get('onset_db', 24), L.get('skip', 0.0)):]
			z = z * (np.abs(y).max() * 10 ** (L['gain_db'] / 20) / np.abs(z).max())
			d = int(L.get('delay', 0.0) * SR)
			n = min(len(z), len(y) - d)
			y = y.copy()
			y[d:d + n] += z[:n]
			info['layer'] = dict(src=L['src'], gain_db=L['gain_db'])
		ln = len(y) / SR
		fo = c['fade'] if c['fade'] else min(max(0.25 * ln, 0.03), 0.25)
		y = fade(y, 0.002, fo)
		y = y * (PEAK / np.abs(y).max())
		need = c['target'] - max_m(y)
		if need > 3.0:                     # transient-heavy: limit into the file instead of a big positive volume_db
			drive = min(need - 2.0, 10.0)
			y = limit(y * 10 ** (drive / 20))
			info['limiter_drive_db'] = round(drive, 1)
		info['trim_start'] = round(on_i / SR, 3)
		e2, _ = env_db(y)
		info['head_silence_ms'] = int(np.argmax(e2 > e2.max() - 30)) * 5
		level = max_m(y)
	write_wav(f'{OUT_SFX}/{name}.wav', y)
	bus, positional, unit, maxd = CAT[c['cat']]
	if name in AMB_3D:
		positional, (unit, maxd) = True, AMB_3D[name]
	vol = float(np.clip(c['target'] - level, -30, 8))
	entry = dict(file=f'sfx/{name}.wav', bus=bus, volume_db=round(vol, 1), pitch_random=c.get('pr', 0.0),
		loop=bool(c.get('loop', False)), max_distance=maxd, unit_size=unit, positional=positional)
	info.update(raw_len=round(raw_len, 3), out_len=round(len(y) / SR, 3), level_db=round(float(level), 1),
		volume_db=entry['volume_db'], peak_dbfs=round(float(20 * np.log10(np.abs(y).max())), 2))
	return entry, info


def loudness(path):
	r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
		capture_output=True, text=True).stderr
	import re
	i = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
	tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
	return i, tp


def process_music(name):
	x = decode(name, hp=25, ch=2)
	m = x.mean(axis=1)
	win = SR // 2
	n = len(m) // win
	e = 20 * np.log10(np.sqrt(np.mean(m[:n * win].reshape(n, win) ** 2, axis=1)) + 1e-9)
	med = np.median(e)
	ef, wf = env_db(m, SR // 20)
	lead = zero_cross_before(m, int(np.argmax(ef > -50)) * wf)   # leading silence goes
	s_i = max(lead, int(np.argmax(e > med - 9)) * win)   # the loop starts after a quiet / fading-in intro ...
	if s_i - lead < SR:
		s_i = lead
	last = int(np.where(e > med - 5)[0][-1])              # ... and ends before the fade-out ending
	e_i = (last + 1) * win
	s_i = zero_cross_before(m, s_i)
	C = 3 * SR
	# intro plays once; at the end playback wraps to loop_offset, where the tail is crossfaded into the loop head
	y = x[lead:e_i - C].copy()
	o = s_i - lead
	t = np.linspace(0, np.pi / 2, C, endpoint=False)[:, None]
	y[o:o + C] = x[s_i:s_i + C] * np.sin(t) + x[e_i - C:e_i] * np.cos(t)
	tmp = f'work/audio/tmp_{name}.wav'
	write_wav(tmp, y * 0.5)
	i0, _ = loudness(tmp)
	gain_db = MUSIC_LUFS - (i0 + 20 * np.log10(2))      # tmp was written at -6.02 dB
	g = 10 ** (gain_db / 20)
	pk = np.abs(y).max() * g
	if pk > 10 ** (-1.0 / 20):                           # keep 1 dB of headroom: trade loudness, never clip
		g *= 10 ** (-1.0 / 20) / pk
	write_wav(tmp, y * g)
	out = f'{OUT_MUS}/{name}.ogg'
	subprocess.check_call([FFMPEG4, '-v', 'error', '-y', '-i', tmp, '-c:a', 'libvorbis', '-q:a', '5', out])
	os.remove(tmp)
	i1, tp1 = loudness(out)
	dec = np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', out, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-']), np.float32).reshape(-1, 2).astype(np.float64)
	entry = dict(file=f'music/{name}.ogg', bus='Music', volume_db=MUSIC_VOL, pitch_random=0.0, loop=True,
		loop_offset=round(o / SR, 4), max_distance=0.0, unit_size=0.0, positional=False)
	info = dict(lead_trim=round(lead / SR, 2), loop_offset=round(o / SR, 3), raw_loop_from=round(s_i / SR, 2),
		raw_loop_to=round(e_i / SR, 2), out_len=round(len(dec) / SR, 2), lufs=i1, true_peak=tp1, seam_wav=seam_check(y, o),
		seam_ogg=seam_check(dec, o), ogg_len_vs_wav=len(dec) - len(y))
	return entry, info


def main():
	os.makedirs(OUT_SFX, exist_ok=True)
	os.makedirs(OUT_MUS, exist_ok=True)
	reg = json.load(open('docs/audio_list.json'))
	# optional names on the command line: rebuild only those, keep every other manifest / report entry (a full run
	# re-encodes the music, and every Vorbis encode gets a new random stream serial = new bytes, same audio)
	only = set(sys.argv[1:])
	manifest, report = {}, {}
	if only:
		manifest = json.load(open('game/assets/audio/audio.json'))['sounds']
		report = json.load(open('work/audio/processed.json')) if os.path.exists('work/audio/processed.json') else {}
	for it in reg['sfx']:
		n = it['name']
		if only and n not in only:
			continue
		c = dict(D)
		c.update(CFG[n])
		manifest[n], report[n] = process_sfx(n, c)
		print(n, report[n])
	for it in reg['music']:
		n = it['name']
		if only and n not in only:
			continue
		manifest[n], report[n] = process_music(n)
		print(n, report[n])
	order = [it['name'] for it in reg['sfx'] + reg['music']]
	manifest = {n: manifest[n] for n in order if n in manifest}
	doc = {'_about': 'Audio manifest read by the Sfx autoload (game/scripts/autoload/sfx.gd). Built by tools/audio/process.py '
		'from art_src/audio/raw (registry: docs/audio_list.json). volume_db is added to every play; positional sounds use '
		'unit_size / max_distance; pitch_random = +- fraction.', 'sounds': manifest}
	json.dump(doc, open('game/assets/audio/audio.json', 'w'), indent=1)
	json.dump(report, open('work/audio/processed.json', 'w'), indent=1)


if __name__ == '__main__':
	main()
