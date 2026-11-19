import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Badge, C, Camera, Count, DISPLAY, FONT, ModelGlyph, Tag, appear, cue, kf, pop, word, rnd} from '../lib';

const Half: React.FC<{f: number; m: 'astra' | 'sol'; side: 'l' | 'r'}> = ({f, m, side}) => {
	const col = m === 'astra' ? C.astra : C.sol, deep = m === 'astra' ? C.astraDeep : C.solDeep;
	const slide = kf(f, [0, 22], [side === 'l' ? -700 : 700, 0]);
	return (
		<div style={{position: 'absolute', inset: 0, transform: `translateX(${slide}px)`,
			clipPath: side === 'l' ? 'polygon(0 0, 54% 0, 46% 100%, 0 100%)' : 'polygon(54% 0, 100% 0, 100% 100%, 46% 100%)'}}>
			<div style={{position: 'absolute', inset: 0, background: side === 'l'
				? `radial-gradient(900px 700px at 25% 45%, ${deep}88, transparent 70%), linear-gradient(160deg, #081a3c, #050a16)`
				: `radial-gradient(900px 700px at 75% 45%, ${deep}88, transparent 70%), linear-gradient(200deg, #2a1504, #0d0804)`}} />
			{/* drifting texture: streaks for Astra, rising embers for Sol */}
			{Array.from({length: 26}).map((_, i) => {
				const x = (side === 'l' ? 0 : 960) + rnd(i + (side === 'l' ? 0 : 50)) * 960;
				const y = m === 'astra' ? rnd(i + 7) * 1080 : (1080 - ((rnd(i + 3) * 1080 + f * (1 + rnd(i) * 2)) % 1180));
				const xx = m === 'astra' ? (x + f * (0.8 + rnd(i + 1) * 1.5)) % 1920 : x;
				return <div key={i} style={{position: 'absolute', left: xx, top: y, width: m === 'astra' ? 60 + rnd(i) * 120 : 5, height: m === 'astra' ? 2 : 5, borderRadius: 4, background: col, opacity: 0.18 + rnd(i + 2) * 0.25}} />;
			})}
		</div>
	);
};

export const Cold: React.FC<{f: number}> = ({f}) => {
	const tHalf = word('gap', 'half'), tPoint = word('gap', 'point');
	const tCost = cue('cost'), tFifth = word('cost', 'fifth'), tAsk = cue('ask');
	const rowShift = kf(f, [tCost - 4, tCost + 14], [0, 1]);
	const ask = kf(f, [tAsk, tAsk + 30], [0, 1]);
	const Side: React.FC<{m: 'astra' | 'sol'; cx: number}> = ({m, cx}) => {
		const col = m === 'astra' ? C.astra : C.sol;
		const isA = m === 'astra';
		const pIn = pop(f, isA ? 8 : 14);
		const score = isA ? 44.2 : 43.8, cost = isA ? 5.97 : 1.29;
		const dim = 1;
		return (
			<Abs x={cx} y={0} w={0} h={1080} style={{opacity: dim}}>
				<Abs x={0} y={165} center style={{transform: `translate(-50%,-50%) scale(${0.6 + 0.4 * pIn})`, opacity: pIn}}><Badge m={m} size={64} full /></Abs>
				{/* score row */}
				<Abs x={0} y={kf(rowShift, [0, 1], [480, 385])} center style={{textAlign: 'center', transform: `translate(-50%,-50%) scale(${1 - rowShift * 0.3})`, opacity: appear(f, tHalf - 6, 8)}}>
					<div style={{fontFamily: FONT, fontSize: 26, letterSpacing: 4, color: C.dim, fontWeight: 600}}>SCORE</div>
					<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 210, lineHeight: 1, color: '#fff', textShadow: `0 0 60px ${col}88`}}>
						<Count f={f} a={tHalf - 6} b={tHalf + 22} to={score} from={30} />
					</div>
				</Abs>
				{/* cost row */}
				<Abs x={0} y={kf(rowShift, [0, 1], [760, 640])} center style={{textAlign: 'center', opacity: appear(f, tCost + 2, 10), transform: `translate(-50%,-50%) translateY(${(1 - appear(f, tCost + 2, 14)) * 40}px)`}}>
					<div style={{fontFamily: FONT, fontSize: 26, letterSpacing: 4, color: C.dim, fontWeight: 600}}>COST PER TASK</div>
					<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 170, lineHeight: 1.05, color: col}}>
						<Count f={f} a={tCost + 2} b={tCost + 26} to={cost} dec={2} pre="$" />
					</div>
					<div style={{width: 520, height: 18, borderRadius: 9, background: 'rgba(255,255,255,0.08)', margin: '14px auto 0', overflow: 'hidden'}}>
						<div style={{height: '100%', width: `${kf(f, [tCost + 4, tCost + 30], [0, isA ? 100 : 21.6])}%`, background: col, borderRadius: 9}} />
					</div>
				</Abs>
			</Abs>
		);
	};
	const gapP = pop(f, tPoint), fifthP = pop(f, tFifth);
	return (
		<AbsoluteFill>
			<Camera style={{opacity: 1 - ask * 0.62, filter: ask > 0.02 ? `blur(${ask * 5}px)` : undefined}} f={f} keys={[[0, {s: 1.06, x: 960, y: 540}], [tAsk - 10, {s: 1.0, x: 960, y: 540}], [tAsk + 60, {s: 1.12, x: 880, y: 540, r: -0.8}]]}>
				<Half f={f} m="astra" side="l" />
				<Half f={f} m="sol" side="r" />
				{/* divider */}
				<div style={{position: 'absolute', left: 960, top: -60, width: 4, height: 1200, background: `linear-gradient(${C.astra}, #fff, ${C.sol})`, transform: `rotate(${4.3 + Math.sin(f / 22) * 0.6}deg)`, boxShadow: '0 0 30px rgba(255,255,255,0.5)', opacity: appear(f, 10)}} />
				<Side m="astra" cx={500} />
				<Side m="sol" cx={1420} />
				{/* centre chips */}
				<Abs x={960} y={kf(rowShift, [0, 1], [490, 395])} center style={{opacity: Math.min(1, gapP * 1.4), transform: `translate(-50%,-50%) scale(${0.5 + 0.5 * gapP})`}}>
					<div style={{padding: '18px 30px', borderRadius: 20, background: '#fff', color: '#0A0F1C', fontFamily: DISPLAY, fontWeight: 800, fontSize: 44, textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.5)'}}>
						0.4<div style={{fontSize: 20, letterSpacing: 3, fontFamily: FONT, fontWeight: 700}}>POINTS APART</div>
					</div>
				</Abs>
				<Abs x={960} y={kf(rowShift, [0, 1], [760, 640])} center style={{opacity: Math.min(1, fifthP * 1.4), transform: `translate(-50%,-50%) scale(${0.5 + 0.5 * fifthP})`}}>
					<div style={{padding: '18px 30px', borderRadius: 20, background: C.sol, color: '#1B0F02', fontFamily: DISPLAY, fontWeight: 800, fontSize: 44, textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.5)'}}>
						≈ ⅕<div style={{fontSize: 20, letterSpacing: 3, fontFamily: FONT, fontWeight: 700}}>THE COST</div>
					</div>
				</Abs>
			</Camera>
			{/* source line (outside camera so it never crops) */}
			<Abs x={960} y={64} center style={{transform: 'translate(-50%,0)', display: 'flex', gap: 16, opacity: appear(f, tHalf - 10)}}>
				<Tag color="#FFFFFF" style={{background: 'rgba(0,0,0,0.45)'}}>OpenAI-reported</Tag>
				<Tag color={C.ink} style={{background: 'rgba(0,0,0,0.45)'}}>FrontierCode 2.0 · both at max</Tag>
			</Abs>
			<Abs x={960} y={840} center style={{transform: 'translate(-50%,0)', opacity: appear(f, tCost + 10) * (1 - ask)}}>
				<div style={{fontFamily: FONT, fontSize: 22, color: C.dim, letterSpacing: 1.5}}>Cost per task on this benchmark</div>
			</Abs>
			{/* the question */}
			<Abs x={960} y={500} center style={{opacity: ask, transform: `translate(-50%,-50%) scale(${0.9 + 0.1 * ask})`, display: 'flex', alignItems: 'center', gap: 26,
				padding: '30px 56px', borderRadius: 24, background: 'rgba(5,10,22,0.88)', border: `2px solid ${C.astra}88`}}>
				<ModelGlyph m="astra" size={74} spin={f * 0.8} />
				<span style={{fontFamily: DISPLAY, fontSize: 78, fontWeight: 800, color: '#fff', whiteSpace: 'nowrap'}}>So when do you need <span style={{color: C.astra}}>Astra</span>?</span>
			</Abs>
		</AbsoluteFill>
	);
};
