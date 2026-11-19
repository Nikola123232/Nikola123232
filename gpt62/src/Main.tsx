import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {C, FONT, TL, TOTAL_FRAMES, kf, rnd, s2f, Tag, easeInOut} from './lib';
import captions from './captions.json';
import {Cold} from './scenes/Cold';
import {Launch} from './scenes/Launch';
import {Bench} from './scenes/Bench';
import {Web} from './scenes/Web';
import {Bug} from './scenes/Bug';
import {Slides} from './scenes/Slides';
import {Verdict} from './scenes/Verdict';

const ORDER = ['cold', 'launch', 'bench', 'web', 'bug', 'slides', 'verdict'] as const;
const SCENES: Record<string, React.FC<{f: number}>> = {cold: Cold, launch: Launch, bench: Bench, web: Web, bug: Bug, slides: Slides, verdict: Verdict};
const LABEL: Record<string, string> = {launch: '01 · What launched', bench: '02 · The FrontierCode result', web: '03 · Scenario: a website', bug: '04 · Scenario: a hard bug', slides: '05 · Scenario: a slide deck', verdict: '06 · The verdict'};
const ILLUSTRATIVE = new Set(['web', 'bug', 'slides']);

// section windows: boundaries halfway between one section's last line and the next one's first line
export const BOUNDS: Record<string, [number, number]> = {};
ORDER.forEach((s, i) => {
	const a = i === 0 ? 0 : Math.round((s2f(TL.sections[ORDER[i - 1]][1]) + s2f(TL.sections[s][0])) / 2);
	const b = i === ORDER.length - 1 ? TOTAL_FRAMES : Math.round((s2f(TL.sections[s][1]) + s2f(TL.sections[ORDER[i + 1]][0])) / 2);
	BOUNDS[s] = [a, b];
});

const Background: React.FC<{f: number}> = ({f}) => {
	const drift = f * 0.6;
	return (
		<AbsoluteFill style={{background: `radial-gradient(1400px 900px at 50% 40%, ${C.bg2}, ${C.bg})`}}>
			{/* perspective floor grid */}
			<div style={{position: 'absolute', left: -960, top: 560, width: 3840, height: 1400, transform: 'perspective(900px) rotateX(72deg)', transformOrigin: '50% 0%',
				backgroundImage: `linear-gradient(${C.line} 1.5px, transparent 1.5px), linear-gradient(90deg, ${C.line} 1.5px, transparent 1.5px)`,
				backgroundSize: '120px 120px', backgroundPosition: `0px ${drift}px`, opacity: 0.55,
				maskImage: 'linear-gradient(to bottom, transparent, black 25%, black 60%, transparent)', WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 30%, transparent 90%)'}} />
			{/* floating dust, three parallax layers */}
			{Array.from({length: 46}).map((_, i) => {
				const layer = i % 3, sp = [0.15, 0.35, 0.7][layer];
				const x = (rnd(i) * 2100 - f * sp * (rnd(i + 9) > 0.5 ? 1 : -0.6)) % 2100;
				const y = rnd(i + 3) * 1080 + Math.sin(f / 60 + i) * 10;
				const r = [1.5, 2.5, 4][layer];
				return <div key={i} style={{position: 'absolute', left: (x + 2100) % 2100 - 90, top: y, width: r, height: r, borderRadius: 9, background: i % 5 === 0 ? C.sol : C.astraHi, opacity: [0.25, 0.35, 0.18][layer]}} />;
			})}
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55))'}} />
		</AbsoluteFill>
	);
};

const SceneWindow: React.FC<{f: number; name: string}> = ({f, name}) => {
	const [a, b] = BOUNDS[name];
	if (f < a - 10 || f > b + 10) return null;
	const S = SCENES[name];
	// whip transition: outgoing slides left, incoming arrives from the right
	const inP = name === 'cold' ? 1 : kf(f, [a - 4, a + 10], [0, 1], easeInOut);
	const outP = name === 'verdict' ? 0 : kf(f, [b - 9, b + 4], [0, 1], easeInOut);
	const x = (1 - inP) * 380 - outP * 380;
	const op = Math.min(inP, 1 - outP);
	return (
		<AbsoluteFill style={{opacity: op, transform: `translateX(${x}px) scale(${1 + (1 - inP) * 0.06 + outP * 0.04})`, filter: op < 0.97 ? `blur(${(1 - op) * 10}px)` : undefined}}>
			<S f={f} />
		</AbsoluteFill>
	);
};

const Streak: React.FC<{f: number}> = ({f}) => {
	const hits = ORDER.slice(1).map((s) => BOUNDS[s][0]);
	const near = hits.find((h) => f >= h - 8 && f <= h + 8);
	if (near === undefined) return null;
	const p = (f - (near - 8)) / 16;
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			<div style={{position: 'absolute', top: 0, bottom: 0, left: kf(p, [0, 1], [2200, -900]), width: 520, transform: 'skewX(-18deg)',
				background: `linear-gradient(90deg, transparent, ${C.astra}33, ${C.sol}44, transparent)`, opacity: Math.sin(p * Math.PI)}} />
		</AbsoluteFill>
	);
};

const HUD: React.FC<{f: number}> = ({f}) => {
	const cur = ORDER.find((s) => f >= BOUNDS[s][0] && f < BOUNDS[s][1]) ?? 'verdict';
	const [a, b] = BOUNDS[cur];
	const op = Math.min(kf(f, [a + 8, a + 22], [0, 1]), kf(f, [b - 12, b - 2], [1, 0]));
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			{LABEL[cur] && (
				<div style={{position: 'absolute', left: 48, top: 40, opacity: op, transform: `translateX(${(1 - op) * -20}px)`, fontFamily: FONT, fontWeight: 700, fontSize: 24, letterSpacing: 2.5, textTransform: 'uppercase', color: C.ink,
					display: 'flex', alignItems: 'center', gap: 14, background: 'rgba(6,10,19,0.72)', padding: '10px 20px', borderRadius: 12}}>
					<span style={{width: 34, height: 4, borderRadius: 4, background: `linear-gradient(90deg, ${C.astra}, ${C.sol})`}} />
					<span style={{textShadow: '0 2px 10px rgba(0,0,0,0.6)'}}>{LABEL[cur]}</span>
				</div>
			)}
			{ILLUSTRATIVE.has(cur) && (
				<div style={{position: 'absolute', right: 64, top: 44, opacity: op}}>
					<Tag color="#E6EAF2" style={{background: 'rgba(6,10,19,0.75)'}}>Illustrative example</Tag>
				</div>
			)}
		</AbsoluteFill>
	);
};

type Cap = {s: number; e: number; text: string};
const Captions: React.FC<{f: number}> = ({f}) => {
	const t = f / 30;
	const c = (captions as Cap[]).find((x) => t >= x.s && t < x.e);
	if (!c) return null;
	const op = Math.min(kf(t, [c.s, c.s + 0.1], [0, 1]), kf(t, [c.e - 0.06, c.e], [1, 0.4]));
	return (
		<div style={{position: 'absolute', left: 0, right: 0, bottom: 54, display: 'flex', justifyContent: 'center', opacity: op}}>
			<div style={{maxWidth: 1500, padding: '12px 30px', borderRadius: 16, background: 'rgba(3,6,12,0.78)', color: '#FFFFFF', fontFamily: FONT, fontWeight: 600, fontSize: 42, lineHeight: 1.25, textAlign: 'center', letterSpacing: 0.2}}>
				{c.text}
			</div>
		</div>
	);
};

export const Main: React.FC = () => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: C.bg, fontFamily: FONT, color: C.ink}}>
			<Background f={f} />
			{ORDER.map((s) => <SceneWindow key={s} f={f} name={s} />)}
			<Streak f={f} />
			<HUD f={f} />
			<Captions f={f} />
			{/* gentle film grain-free fade in/out at the very ends */}
			<AbsoluteFill style={{background: '#000', opacity: Math.max(kf(f, [0, 6], [1, 0]), kf(f, [TOTAL_FRAMES - 14, TOTAL_FRAMES - 1], [0, 1]))}} />
		</AbsoluteFill>
	);
};
