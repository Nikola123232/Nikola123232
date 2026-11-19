import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Badge, C, Camera, DISPLAY, FONT, ModelGlyph, Panel, Tag, appear, cue, kf, life, pop, word, wordAfter, easeInOut} from '../lib';

const Card: React.FC<{f: number; m: 'astra' | 'sol'; x: number; y: number; s: number; ry: number; op: number; line: string}> = ({f, m, x, y, s, ry, op, line}) => {
	const col = m === 'astra' ? C.astra : C.sol;
	return (
		<Abs x={x} y={y} center style={{opacity: op, transform: `translate(-50%,-50%) perspective(1400px) rotateY(${ry}deg) scale(${s})`}}>
			<Panel glow={col} style={{width: 520, height: 600, padding: 44, boxSizing: 'border-box', position: 'relative', overflow: 'hidden',
				background: m === 'astra' ? 'linear-gradient(160deg, #0F2550, #070D1C 70%)' : 'linear-gradient(160deg, #4A2606, #120A04 70%)'}}>
				<div style={{position: 'absolute', right: -90, top: -90, opacity: 0.2}}><ModelGlyph m={m} size={380} spin={f * 0.15} /></div>
				<div style={{fontFamily: FONT, fontSize: 24, letterSpacing: 4, color: C.dim, fontWeight: 700}}>GPT-6.2</div>
				<div style={{fontFamily: DISPLAY, fontSize: 116, fontWeight: 800, color: col, lineHeight: 1.05, marginTop: 6}}>{m === 'astra' ? 'Astra' : 'Sol'}</div>
				<div style={{fontFamily: FONT, fontSize: 34, color: C.ink, fontWeight: 600, marginTop: 30}}>{m === 'astra' ? 'The flagship' : 'The efficient one'}</div>
				<div style={{fontFamily: FONT, fontSize: 28, color: C.dim, marginTop: 14, lineHeight: 1.35}}>{line}</div>
				<div style={{position: 'absolute', left: 44, bottom: 44}}><ModelGlyph m={m} size={70} /></div>
			</Panel>
		</Abs>
	);
};

/** Astra workload: a long chain of dependent steps; one bad assumption propagates */
const Chain: React.FC<{f: number; a: number; bad: number}> = ({f, a, bad}) => {
	const N = 9;
	const pts = Array.from({length: N}).map((_, i) => ({x: 120 + (i % 3) * 250 + (Math.floor(i / 3) % 2 ? 0 : 0), y: 90 + Math.floor(i / 3) * 190}));
	// snake order
	const order = [0, 1, 2, 5, 4, 3, 6, 7, 8].map((k) => pts[k]);
	const labels = ['Read spec', 'Plan', 'Schema', 'API layer', 'Migration', 'Tests', 'UI wiring', 'Docs', 'Ship'];
	return (
		<div style={{position: 'relative', width: 760, height: 560}}>
			<svg width={760} height={560} style={{position: 'absolute', inset: 0}}>
				{order.slice(1).map((p, i) => {
					const q = order[i], vis = appear(f, a + i * 5, 10), red = f > bad + 8 + (i - 2) * 4 && i >= 2;
					return <line key={i} x1={q.x} y1={q.y} x2={q.x + (p.x - q.x) * vis} y2={q.y + (p.y - q.y) * vis} stroke={red ? C.red : C.astra} strokeWidth={4} strokeOpacity={0.7} strokeDasharray={red ? '0' : '10 8'} />;
				})}
			</svg>
			{order.map((p, i) => {
				const pp = pop(f, a + i * 5), red = i === 2 ? f > bad : f > bad + 8 + (i - 3) * 4 && i > 2;
				return (
					<div key={i} style={{position: 'absolute', left: p.x, top: p.y, transform: `translate(-50%,-50%) scale(${pp})`, padding: '14px 20px', borderRadius: 14, minWidth: 150, textAlign: 'center',
						background: red ? '#3A0D12' : '#0E1F40', border: `2px solid ${red ? C.red : C.astra}`, color: red ? '#FFC9CB' : C.ink, fontFamily: FONT, fontWeight: 600, fontSize: 24}}>
						{labels[i]}{i === 2 && f > bad ? <div style={{fontSize: 18, color: C.red, marginTop: 2}}>wrong assumption</div> : null}
					</div>
				);
			})}
		</div>
	);
};

const Everyday: React.FC<{f: number; a: number}> = ({f, a}) => {
	const items = ['Draft an email', 'Summarize notes', 'Fix a small bug', 'Write unit tests', 'Clean up a CSV', 'Rename a function'];
	return (
		<div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22, width: 760}}>
			{items.map((t, i) => {
				const p = pop(f, a + i * 4), done = f > a + 14 + i * 6;
				return (
					<div key={i} style={{transform: `scale(${p})`, opacity: p, display: 'flex', alignItems: 'center', gap: 18, padding: '24px 26px', borderRadius: 18, background: '#24160A', border: `2px solid ${done ? C.sol : '#5a3d1c'}`,
						fontFamily: FONT, fontSize: 28, fontWeight: 600, color: C.ink}}>
						<div style={{width: 40, height: 40, borderRadius: 40, flexShrink: 0, background: done ? C.sol : 'transparent', border: `3px solid ${C.sol}`, color: '#1B0F02', fontSize: 26, fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{done ? '✓' : ''}</div>
						{t}
					</div>
				);
			})}
		</div>
	);
};

const PriceBars: React.FC<{f: number; a: number; tSol: number; tQ: number}> = ({f, a, tSol, tQ}) => {
	const H = 520 / 40; // px per dollar
	const Bar: React.FC<{v: number; m: 'astra' | 'sol'; at: number}> = ({v, m, at}) => {
		const p = kf(f, [at, at + 20], [0, 1]);
		const col = m === 'astra' ? C.astra : C.sol;
		return (
			<div style={{width: 150, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: 600}}>
				<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 50, color: col, opacity: appear(f, at + 10), marginBottom: 10}}>${v}</div>
				<div style={{width: 130, height: Math.max(4, v * H * p), borderRadius: '14px 14px 4px 4px', background: `linear-gradient(${m === 'astra' ? C.astraHi : C.solHi}, ${col})`, boxShadow: `0 0 40px ${col}55`}} />
			</div>
		);
	};
	const g = (label: string, va: number, vs: number, d: number) => (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
			<div style={{display: 'flex', gap: 30, alignItems: 'flex-end'}}><Bar v={va} m="astra" at={a + d} /><Bar v={vs} m="sol" at={tSol + d / 2} /></div>
			<div style={{height: 3, width: 360, background: C.line, marginTop: 0}} />
			<div style={{fontFamily: FONT, fontSize: 30, fontWeight: 700, color: C.ink, marginTop: 16, letterSpacing: 2}}>{label}</div>
		</div>
	);
	const q = pop(f, tQ);
	return (
		<div style={{position: 'relative', display: 'flex', gap: 140, alignItems: 'flex-end'}}>
			{g('INPUT', 8, 2, 0)}
			{g('OUTPUT', 40, 10, 18)}
			<div style={{position: 'absolute', right: -380, top: 150, opacity: Math.min(1, q * 1.4), transform: `scale(${0.4 + 0.6 * q}) rotate(${-6 + (1 - q) * 20}deg)`, padding: '24px 36px', borderRadius: 22, border: `4px solid ${C.sol}`, color: C.sol, fontFamily: DISPLAY, fontWeight: 800, fontSize: 64, textAlign: 'center', background: 'rgba(30,18,4,0.9)'}}>
				¼<div style={{fontSize: 26, fontFamily: FONT, letterSpacing: 2}}>THE PRICE PER TOKEN</div>
			</div>
		</div>
	);
};

export const Launch: React.FC<{f: number}> = ({f}) => {
	const L0 = cue('launch'), tA = cue('astra'), tS = cue('sol'), tP0 = cue('price0'), tP = cue('price'), tPS = cue('pricesol'), tQ = cue('quarter'), tW = cue('why'), tSW = cue('solwhy'), tAW = cue('astrawhy');
	const tAssume = wordAfter('assumption', tA);
	// card choreography
	const aExp = kf(f, [tA - 6, tA + 16], [0, 1], easeInOut), sExp = kf(f, [tS - 6, tS + 16], [0, 1], easeInOut);
	const toPrice = kf(f, [tP0 - 8, tP0 + 10], [0, 1], easeInOut);
	const astraX = kf(f, [L0, L0 + 24], [700, 560]) - aExp * 0 + sExp * -900;
	const solX = kf(f, [L0 + 6, L0 + 30], [1220, 1360]) + aExp * 900 - sExp * 1700;
	const cardsOp = (1 - toPrice);
	const cardIn = pop(f, L0 + 4), cardIn2 = pop(f, L0 + 10);
	const titleOp = 1 - aExp;
	return (
		<AbsoluteFill>
			<Camera f={f} keys={[[L0, {s: 1.08}], [tA, {s: 1}], [tA + 40, {s: 1.04, x: 900}], [tS, {s: 1.04, x: 900}], [tS + 40, {s: 1.02, x: 940}], [tP0, {s: 1}], [tW, {s: 1.05}], [tW + 1, {s: 1.0}]]}>
				{/* title */}
				<Abs x={960} y={250} center style={{opacity: titleOp, textAlign: 'center', transform: `translate(-50%,-50%) translateY(${aExp * -60}px)`}}>
					<div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 150, letterSpacing: -2, color: '#fff', opacity: appear(f, L0), lineHeight: 1}}>GPT-6.2</div>
					<div style={{marginTop: 18, opacity: appear(f, word('launch', 'november'))}}><Tag color={C.ink}>Released November 17, 2026</Tag></div>
				</Abs>
				<Card f={f} m="astra" x={astraX} y={kf(aExp, [0, 1], [650, 520])} s={(0.62 + 0.38 * cardIn) * kf(aExp, [0, 1], [0.7, 1])} ry={kf(f, [L0, L0 + 24], [35, 10]) - aExp * 10} op={Math.min(cardIn, cardsOp)} line="For the hardest projects" />
				<Card f={f} m="sol" x={solX} y={kf(Math.max(aExp, sExp), [0, 1], [650, 520])} s={(0.62 + 0.38 * cardIn2) * kf(sExp, [0, 1], [0.7, 1])} ry={kf(f, [L0, L0 + 30], [-35, -10]) + sExp * 10} op={Math.min(cardIn2, cardsOp)} line="Built for everyday work" />
				{/* astra workload */}
				<Abs x={1260} y={520} center style={{opacity: life(f, tA + 6, tS + 4), transform: `translate(-50%,-50%) translateX(${(1 - appear(f, tA + 6, 18)) * 120}px)`}}>
					<div style={{fontFamily: FONT, fontSize: 28, color: C.astraHi, fontWeight: 700, letterSpacing: 2, marginBottom: 6}}>LONG, MESSY, CONNECTED WORK</div>
					<Chain f={f} a={tA + 8} bad={tAssume} />
				</Abs>
				{/* sol workload */}
				<Abs x={1260} y={540} center style={{opacity: life(f, tS + 6, tP0 + 4), transform: `translate(-50%,-50%) translateX(${(1 - appear(f, tS + 6, 18)) * 120}px)`}}>
					<div style={{fontFamily: FONT, fontSize: 28, color: C.solHi, fontWeight: 700, letterSpacing: 2, marginBottom: 20}}>QUICK, EVERYDAY TASKS</div>
					<Everyday f={f} a={tS + 8} />
				</Abs>
				{/* prices */}
				<Abs x={800} y={500} center style={{opacity: life(f, tP0 + 2, tW + 2)}}>
					<div style={{textAlign: 'left', marginBottom: 10}}><Tag color={C.ink}>API price · per 1M tokens</Tag></div>
					<div style={{display: 'flex', gap: 30, marginBottom: 6, opacity: appear(f, tP)}}><Badge m="astra" size={34} /><Badge m="sol" size={34} /></div>
					<PriceBars f={f} a={tP + 8} tSol={tPS} tQ={tQ} />
				</Abs>
			</Camera>
			{/* why each matters: split */}
			<WhySplit f={f} a={tW} tSW={tSW} tAW={tAW} />
		</AbsoluteFill>
	);
};

const WhySplit: React.FC<{f: number; a: number; tSW: number; tAW: number}> = ({f, a, tSW, tAW}) => {
	const op = appear(f, a, 14);
	if (op <= 0) return null;
	const sp = appear(f, tSW, 14), ap = appear(f, tAW, 14);
	return (
		<AbsoluteFill style={{opacity: op}}>
			<Abs x={960} y={150} center style={{fontFamily: DISPLAY, fontSize: 60, fontWeight: 800, color: '#fff', opacity: op}}>Why each one matters</Abs>
			{/* Sol: more jobs per budget */}
			<Abs x={500} y={540} center style={{opacity: sp, transform: `translate(-50%,-50%) translateY(${(1 - sp) * 40}px)`}}>
				<Panel glow={C.sol} style={{width: 720, height: 520, padding: 40, boxSizing: 'border-box'}}>
					<Badge m="sol" size={46} />
					<div style={{fontFamily: FONT, fontSize: 32, color: C.ink, fontWeight: 600, margin: '18px 0 26px'}}>Lots of routine jobs</div>
					{(['sol', 'astra'] as const).map((m, r) => (
						<div key={m} style={{display: 'flex', alignItems: 'center', gap: 14, marginBottom: 22}}>
							<div style={{width: 110, fontFamily: FONT, fontSize: 24, color: C.dim}}>{m === 'sol' ? 'Sol' : 'Astra'}</div>
							{Array.from({length: m === 'sol' ? 4 : 1}).map((_, i) => {
								const p = pop(f, tSW + 10 + i * 7 + r * 30);
								return <div key={i} style={{width: 100, height: 70, borderRadius: 12, background: m === 'sol' ? C.sol : C.astra, opacity: 0.9, transform: `scale(${p})`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0a0f1c', fontWeight: 800, fontFamily: FONT, fontSize: 22}}>JOB</div>;
							})}
						</div>
					))}
					<div style={{fontFamily: FONT, fontSize: 24, color: C.dim, marginTop: 6}}>Same budget, at list price per token</div>
				</Panel>
			</Abs>
			{/* Astra: has to be right */}
			<Abs x={1420} y={540} center style={{opacity: ap, transform: `translate(-50%,-50%) translateY(${(1 - ap) * 40}px)`}}>
				<Panel glow={C.astra} style={{width: 720, height: 520, padding: 40, boxSizing: 'border-box', position: 'relative'}}>
					<Badge m="astra" size={46} />
					<div style={{fontFamily: FONT, fontSize: 32, color: C.ink, fontWeight: 600, margin: '18px 0 0'}}>One job that has to be right</div>
					<svg width={300} height={300} viewBox="-150 -150 300 300" style={{position: 'absolute', left: 210, top: 190}}>
						{[130, 95, 60, 25].map((r, i) => <circle key={r} r={r * kf(f, [tAW + 6 + i * 3, tAW + 20 + i * 3], [0, 1])} fill="none" stroke={C.astra} strokeWidth={6} opacity={0.35 + i * 0.18} />)}
						<path d="M-30,0 L-8,24 L36,-26" fill="none" stroke="#fff" strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={120} strokeDashoffset={120 * (1 - kf(f, [tAW + 30, tAW + 46], [0, 1]))} />
					</svg>
				</Panel>
			</Abs>
		</AbsoluteFill>
	);
};
