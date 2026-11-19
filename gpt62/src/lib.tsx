import React from 'react';
import {Easing, interpolate, spring} from 'remotion';
import timeline from './timeline.json';

export const FPS = 30;
type Word = {w: string; s: number; e: number};
type Line = {section: string; text: string; cue: string | null; start: number; end: number; words: Word[]};
export const TL = timeline as unknown as {total: number; lines: Line[]; sections: Record<string, [number, number]>; cues: Record<string, [number, number]>};
export const s2f = (s: number) => Math.round(s * FPS);
export const TOTAL_FRAMES = Math.ceil(TL.total * FPS);

/** frame at which the line tagged `name` starts */
export const cue = (name: string) => {
	const c = TL.cues[name];
	if (!c) throw new Error('missing cue ' + name);
	return s2f(c[0]);
};
export const cueEnd = (name: string) => s2f(TL.cues[name][1]);
/** frame at which a word (prefix match, case-insensitive) is spoken within a cue line */
export const word = (name: string, w: string, nth = 0) => {
	const line = TL.lines.find((l) => l.cue === name);
	if (!line) throw new Error('missing cue ' + name);
	const hits = line.words.filter((x) => x.w.toLowerCase().replace(/[^a-z0-9$.-]/g, '').startsWith(w.toLowerCase()));
	if (!hits[nth]) throw new Error(`missing word ${w} in ${name}`);
	return s2f(hits[nth].s);
};
export const secStart = (s: string) => s2f(TL.sections[s][0]);
export const secEnd = (s: string) => s2f(TL.sections[s][1]);

export const C = {
	bg: '#060A13',
	bg2: '#0B1222',
	ink: '#EEF2F9',
	dim: '#8C98B0',
	faint: '#4A5670',
	astra: '#4DA8FF',
	astraHi: '#9FD0FF',
	astraDeep: '#1B4FBF',
	sol: '#FFB238',
	solHi: '#FFD58A',
	solDeep: '#D9700F',
	red: '#FF5A60',
	green: '#38D99A',
	panel: 'rgba(16,24,42,0.86)',
	line: 'rgba(150,175,220,0.16)',
};
export const FONT = "'Inter', 'DejaVu Sans', sans-serif";
export const DISPLAY = "'Inter Display', 'Inter', sans-serif";
export const MONO = "'JetBrains Mono', 'DejaVu Sans Mono', monospace";

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);
export const kf = (f: number, frames: number[], values: number[], easing = ease) =>
	interpolate(f, frames, values, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing});
export const appear = (f: number, at: number, dur = 12) => kf(f, [at, at + dur], [0, 1]);
export const pop = (f: number, at: number, stiff = 170) =>
	spring({frame: f - at, fps: FPS, config: {damping: 15, stiffness: stiff, mass: 0.7}});
/** fade in at `a`, fade out at `b` */
export const life = (f: number, a: number, b = 1e9, din = 10, dout = 10) =>
	Math.min(kf(f, [a, a + din], [0, 1]), kf(f, [b - dout, b], [1, 0]));

type Cam = {x?: number; y?: number; s?: number; r?: number; ry?: number; rx?: number};
/** Virtual camera: keys are [frame, {x,y (world point at screen centre), s (zoom), r (roll deg)}] */
export const Camera: React.FC<{f: number; keys: [number, Cam][]; children: React.ReactNode; easing?: (t: number) => number; style?: React.CSSProperties}> = ({f, keys, children, easing = easeInOut, style}) => {
	const fr = keys.map((k) => k[0]);
	const g = (p: keyof Cam, d: number) => (keys.length === 1 ? keys[0][1][p] ?? d : kf(f, fr, keys.map((k) => k[1][p] ?? d), easing));
	const x = g('x', 960), y = g('y', 540), s = g('s', 1), r = g('r', 0), ry = g('ry', 0), rx = g('rx', 0);
	return (
		<div style={{position: 'absolute', inset: 0, perspective: 1800, overflow: 'hidden', ...style}}>
			<div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transformOrigin: '0 0', transformStyle: 'preserve-3d',
				transform: `translate(960px,540px) rotateX(${rx}deg) rotateY(${ry}deg) rotate(${r}deg) scale(${s}) translate(${-x}px,${-y}px)`}}>
				{children}
			</div>
		</div>
	);
};

export const Abs: React.FC<{x: number; y: number; w?: number; h?: number; style?: React.CSSProperties; children?: React.ReactNode; center?: boolean}> = ({x, y, w, h, style, children, center}) => (
	<div style={{position: 'absolute', left: x, top: y, width: w, height: h, ...(center ? {transform: 'translate(-50%,-50%)'} : {}), ...style}}>{children}</div>
);

/** Small pill label, e.g. "OpenAI-reported" */
export const Tag: React.FC<{children: React.ReactNode; color?: string; style?: React.CSSProperties; size?: number}> = ({children, color = C.dim, style, size = 22}) => (
	<div style={{display: 'inline-flex', alignItems: 'center', gap: 10, padding: `${size * 0.36}px ${size * 0.8}px`, borderRadius: 999, border: `1.5px solid ${color}55`,
		background: `${color}14`, color, fontFamily: FONT, fontWeight: 600, fontSize: size, letterSpacing: 1.5, textTransform: 'uppercase', whiteSpace: 'nowrap', ...style}}>
		<span style={{width: size * 0.38, height: size * 0.38, borderRadius: 99, background: color, boxShadow: `0 0 12px ${color}`}} />
		{children}
	</div>
);

export const Panel: React.FC<{style?: React.CSSProperties; children?: React.ReactNode; glow?: string}> = ({style, children, glow}) => (
	<div style={{background: C.panel, border: `1.5px solid ${glow ? glow + '66' : C.line}`, borderRadius: 26,
		boxShadow: `0 30px 80px rgba(0,0,0,0.5)${glow ? `, 0 0 60px ${glow}22, inset 0 1px 0 ${glow}33` : ', inset 0 1px 0 rgba(255,255,255,0.05)'}`, ...style}}>{children}</div>
);

export const fmt = (v: number, dec: number) => v.toFixed(dec);
/** Counter that rolls up between frames a and b */
export const Count: React.FC<{f: number; a: number; b: number; to: number; dec?: number; pre?: string; post?: string; from?: number}> = ({f, a, b, to, dec = 1, pre = '', post = '', from = 0}) => (
	<span style={{fontVariantNumeric: 'tabular-nums'}}>{pre}{fmt(kf(f, [a, b], [from, to], Easing.out(Easing.cubic)), dec)}{post}</span>
);

/** Model badge */
export const Badge: React.FC<{m: 'astra' | 'sol'; size?: number; style?: React.CSSProperties; full?: boolean}> = ({m, size = 30, style, full}) => {
	const col = m === 'astra' ? C.astra : C.sol;
	return (
		<div style={{display: 'inline-flex', alignItems: 'center', gap: size * 0.4, fontFamily: DISPLAY, fontWeight: 800, fontSize: size, color: col, letterSpacing: 0.5, whiteSpace: 'nowrap', ...style}}>
			<ModelGlyph m={m} size={size * 1.1} />
			<span>{full ? 'GPT-6.2 ' : ''}{m === 'astra' ? 'Astra' : 'Sol'}</span>
		</div>
	);
};
/** Original glyphs: Astra = four-point star, Sol = sun disc with rays */
export const ModelGlyph: React.FC<{m: 'astra' | 'sol'; size?: number; spin?: number}> = ({m, size = 40, spin = 0}) =>
	m === 'astra' ? (
		<svg width={size} height={size} viewBox="-50 -50 100 100" style={{transform: `rotate(${spin}deg)`, overflow: 'visible'}}>
			<defs><radialGradient id="ag"><stop offset="0" stopColor="#fff" /><stop offset="0.45" stopColor={C.astraHi} /><stop offset="1" stopColor={C.astra} /></radialGradient></defs>
			<path d="M0,-48 C6,-10 10,-6 48,0 C10,6 6,10 0,48 C-6,10 -10,6 -48,0 C-10,-6 -6,-10 0,-48Z" fill="url(#ag)" />
		</svg>
	) : (
		<svg width={size} height={size} viewBox="-50 -50 100 100" style={{transform: `rotate(${spin}deg)`, overflow: 'visible'}}>
			<defs><radialGradient id="sg"><stop offset="0" stopColor="#FFF4D6" /><stop offset="0.6" stopColor={C.solHi} /><stop offset="1" stopColor={C.sol} /></radialGradient></defs>
			{Array.from({length: 12}).map((_, i) => (
				<rect key={i} x={-4} y={-49} width={8} height={14} rx={4} fill={C.sol} transform={`rotate(${i * 30})`} />
			))}
			<circle r={27} fill="url(#sg)" />
		</svg>
	);

/** Big recommendation card used at the end of each scenario */
export const Pick: React.FC<{f: number; at: number; m: 'astra' | 'sol'; reason: string; x?: number; y?: number; scale?: number}> = ({f, at, m, reason, x = 960, y = 540, scale = 1}) => {
	const p = pop(f, at, 150);
	const col = m === 'astra' ? C.astra : C.sol;
	return (
		<Abs x={x} y={y} center style={{opacity: Math.min(1, p * 1.5), transform: `translate(-50%,-50%) scale(${(0.7 + 0.3 * p) * scale}) rotate(${(1 - p) * -4}deg)`}}>
			<Panel glow={col} style={{padding: '34px 54px', display: 'flex', alignItems: 'center', gap: 40, background: 'rgba(10,16,30,0.94)'}}>
				<div style={{fontFamily: FONT, fontSize: 24, fontWeight: 700, letterSpacing: 3, color: C.dim, textTransform: 'uppercase', writingMode: 'vertical-rl', transform: 'rotate(180deg)'}}>Pick</div>
				<div>
					<Badge m={m} size={86} />
					<div style={{fontFamily: FONT, fontSize: 32, color: C.ink, marginTop: 12, fontWeight: 500, maxWidth: 640}}>{reason}</div>
				</div>
			</Panel>
		</Abs>
	);
};

/** deterministic pseudo random */
export const rnd = (i: number) => {
	const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};

/** first occurrence of a word (prefix match) at or after frame `after` — for lines without a cue tag */
export const wordAfter = (w: string, after = 0) => {
	for (const l of TL.lines) for (const x of l.words) if (s2f(x.s) >= after && x.w.toLowerCase().replace(/[^a-z0-9$.-]/g, '').startsWith(w.toLowerCase())) return s2f(x.s);
	throw new Error('missing word ' + w);
};
