import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Badge, C, Camera, Count, DISPLAY, FONT, MONO, ModelGlyph, Panel, Tag, appear, cue, kf, life, pop, word, wordAfter, easeInOut} from '../lib';

const ReportedTag: React.FC<{extra: string}> = ({extra}) => (
	<div style={{display: 'flex', gap: 14}}>
		<Tag color="#FFFFFF">OpenAI-reported</Tag>
		<Tag color={C.dim}>{extra}</Tag>
	</div>
);

/** A generic code-review card (no real product branding) */
const PRCard: React.FC<{f: number; tRuns: number; tMerge: number}> = ({f, tRuns, tMerge}) => {
	const diff = [
		['-', 'total = sum(items) - discount'],
		['+', 'subtotal = sum(i.price * i.qty for i in items)'],
		['+', 'total = max(0, subtotal - discount)'],
		[' ', 'return round_money(total)'],
	];
	const mp = pop(f, tMerge + 6);
	return (
		<Panel style={{width: 980, padding: 0, overflow: 'hidden'}}>
			<div style={{padding: '24px 34px', borderBottom: `1.5px solid ${C.line}`, display: 'flex', alignItems: 'center', gap: 18}}>
				<div style={{width: 18, height: 18, borderRadius: 18, background: C.green}} />
				<div style={{fontFamily: FONT, fontSize: 30, fontWeight: 700}}>Fix negative totals when discount exceeds subtotal</div>
			</div>
			<div style={{padding: '22px 34px', fontFamily: MONO, fontSize: 25, lineHeight: 1.7}}>
				{diff.map(([k, t], i) => (
					<div key={i} style={{opacity: appear(f, cue('fc') + 6 + i * 5), background: k === '+' ? 'rgba(56,217,154,0.12)' : k === '-' ? 'rgba(255,90,96,0.12)' : 'transparent', color: k === '+' ? '#9FF0CB' : k === '-' ? '#FFB3B6' : C.dim, padding: '0 12px', borderRadius: 6}}>
						{k} {t}
					</div>
				))}
			</div>
			<div style={{padding: '20px 34px 28px', display: 'flex', gap: 20, alignItems: 'center', borderTop: `1.5px solid ${C.line}`}}>
				<div style={{opacity: appear(f, tRuns), transform: `scale(${0.8 + 0.2 * pop(f, tRuns)})`, padding: '12px 22px', borderRadius: 12, background: 'rgba(56,217,154,0.12)', color: C.green, fontFamily: FONT, fontWeight: 700, fontSize: 26}}>✓ Tests pass</div>
				<div style={{opacity: appear(f, tRuns + 18), fontFamily: FONT, fontSize: 26, color: C.dim}}>…but is it good enough to merge?</div>
			</div>
			<div style={{position: 'absolute', right: 40, top: 110, opacity: Math.min(1, mp * 1.5), transform: `scale(${1.6 - 0.6 * mp}) rotate(-8deg)`, padding: '16px 30px', border: `5px solid ${C.green}`, borderRadius: 16, color: C.green, fontFamily: DISPLAY, fontWeight: 900, fontSize: 46, background: 'rgba(6,20,14,0.92)'}}>
				MAINTAINER<br />WOULD MERGE
			</div>
		</Panel>
	);
};

const Dial: React.FC<{f: number; at: number; m: 'astra' | 'sol'}> = ({f, at, m}) => {
	const col = m === 'astra' ? C.astra : C.sol;
	const p = kf(f, [at, at + 30], [0, 1]);
	const ang = -120 + 240 * p;
	const arc = (a0: number, a1: number, r: number) => {
		const pt = (a: number) => [Math.sin((a * Math.PI) / 180) * r, -Math.cos((a * Math.PI) / 180) * r];
		const [x0, y0] = pt(a0), [x1, y1] = pt(a1);
		return `M${x0},${y0} A${r},${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1},${y1}`;
	};
	return (
		<div style={{textAlign: 'center'}}>
			<svg width={380} height={330} viewBox="-190 -190 380 330">
				<path d={arc(-120, 120, 150)} stroke="rgba(255,255,255,0.1)" strokeWidth={26} fill="none" strokeLinecap="round" />
				<path d={arc(-120, Math.max(-119, ang), 150)} stroke={col} strokeWidth={26} fill="none" strokeLinecap="round" />
				<line x1={0} y1={0} x2={Math.sin((ang * Math.PI) / 180) * 110} y2={-Math.cos((ang * Math.PI) / 180) * 110} stroke="#fff" strokeWidth={8} strokeLinecap="round" />
				<circle r={16} fill="#fff" />
				<text x={0} y={100} textAnchor="middle" fill={p > 0.95 ? col : C.dim} style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 52}}>{p > 0.95 ? 'MAX' : ''}</text>
			</svg>
			<Badge m={m} size={44} />
		</div>
	);
};

export const Bench: React.FC<{f: number}> = ({f}) => {
	const B = cue('bench'), tFC = cue('fc'), tRuns = cue('runs'), tMerge = cue('merge'), tMax = cue('max');
	const tAS = cue('astrascore'), tSS = cue('solscore'), tGap = cue('gapnum'), tBill = cue('bill'), tAC = cue('astracost'), tSC = cue('solcost'), tFifth = cue('fifth');
	const tSrc = cue('source'), tQuote = cue('quote'), tCav = cue('caveat'), tC1 = cue('cav1'), tC2 = cue('cav2'), tTake = cue('takeaway'), tTake2 = cue('takeaway2'), tWhere = cue('where');
	const tA44 = word('astrascore', '44'), tS43 = word('solscore', '43');
	// ---- score chart geometry (world coordinates)
	const base = 860, ppu = 11; // px per point, 0..50 axis -> 650px
	const hA = 44.2 * ppu, hS = 43.8 * ppu;
	const growA = kf(f, [tA44 - 8, tA44 + 18], [0, 1]), growS = kf(f, [tS43 - 8, tS43 + 18], [0, 1]);
	const zoom = kf(f, [tGap - 2, tGap + 26], [0, 1], easeInOut);
	const xA = 760, xS = 1160;
	return (
		<AbsoluteFill>
			{/* A: what the test measures */}
			<AbsoluteFill style={{opacity: life(f, B - 30, tMax, 6, 10)}}>
				<Camera f={f} keys={[[B - 30, {s: 0.94}], [tMerge, {s: 1.0}], [tMerge + 40, {s: 1.05, y: 570}], [tMax, {s: 1.06, y: 570}]]}>
					<Abs x={960} y={235} center style={{textAlign: 'center', opacity: appear(f, B - 26)}}>
						<div style={{fontFamily: DISPLAY, fontSize: 104, fontWeight: 900, letterSpacing: -1}}>FrontierCode 2.0</div>
						<div style={{marginTop: 10, opacity: appear(f, word('fc', 'cognition'))}}><Tag color={C.ink}>Coding benchmark · run by Cognition</Tag></div>
					</Abs>
					<Abs x={960} y={660} center style={{opacity: appear(f, tFC + 2), transform: `translate(-50%,-50%) translateY(${(1 - appear(f, tFC + 2, 18)) * 60}px)`}}>
						<div style={{position: 'relative'}}><PRCard f={f} tRuns={tRuns} tMerge={tMerge} /></div>
					</Abs>
				</Camera>
			</AbsoluteFill>
			{/* B: max effort dials */}
			<AbsoluteFill style={{opacity: life(f, tMax - 4, tAS - 6, 8, 8)}}>
				<Abs x={960} y={200} center style={{fontFamily: DISPLAY, fontSize: 64, fontWeight: 800}}>Reasoning effort: both at max</Abs>
				<Abs x={600} y={560} center><Dial f={f} at={tMax + 6} m="astra" /></Abs>
				<Abs x={1320} y={560} center><Dial f={f} at={tMax + 14} m="sol" /></Abs>
			</AbsoluteFill>
			{/* C: score chart with zoom on the gap */}
			<AbsoluteFill style={{opacity: life(f, tAS - 8, tBill - 2, 8, 10)}}>
				<Camera f={f} keys={[[tAS - 8, {s: 1, x: 960, y: 540}], [tGap - 2, {s: 1, x: 960, y: 540}], [tGap + 26, {s: 3.6, x: 960, y: base - hA + 6}], [tBill, {s: 3.7, x: 960, y: base - hA + 6}]]}>
					{/* axis grid */}
					{[0, 10, 20, 30, 40, 50].map((v) => (
						<React.Fragment key={v}>
							<div style={{position: 'absolute', left: 560, top: base - v * ppu, width: 800, height: 1.5, background: C.line}} />
							<div style={{position: 'absolute', left: 500, top: base - v * ppu - 16, width: 44, textAlign: 'right', fontFamily: FONT, fontSize: 24, color: C.faint}}>{v}</div>
						</React.Fragment>
					))}
					{[{x: xA, h: hA, g: growA, m: 'astra' as const, v: 44.2, t: tA44}, {x: xS, h: hS, g: growS, m: 'sol' as const, v: 43.8, t: tS43}].map((b) => {
						const col = b.m === 'astra' ? C.astra : C.sol;
						return (
							<React.Fragment key={b.m}>
								<div style={{position: 'absolute', left: b.x - 110, top: base - b.h * b.g, width: 220, height: b.h * b.g, borderRadius: '10px 10px 0 0', background: `linear-gradient(${b.m === 'astra' ? C.astraHi : C.solHi}, ${col} 30%, ${col}55)`, boxShadow: `0 0 50px ${col}55`}} />
								<div style={{position: 'absolute', left: b.x - 150, top: base - b.h * b.g - 110, width: 300, textAlign: 'center', fontFamily: DISPLAY, fontSize: 84, fontWeight: 900, color: '#fff', opacity: appear(f, b.t) * (1 - zoom)}}>
									<Count f={f} a={b.t - 8} b={b.t + 18} to={b.v} from={0} />
								</div>
								<div style={{position: 'absolute', left: b.x - 150, top: base + 20, width: 300, display: 'flex', justifyContent: 'center', opacity: appear(f, b.t - 10)}}><Badge m={b.m} size={40} /></div>
							</React.Fragment>
						);
					})}
					{/* zoomed gap annotation (world units: drawn small so it reads at 3.6x) */}
					<div style={{position: 'absolute', left: xA + 110, top: base - hA, width: xS - xA - 220, height: 1, borderTop: `1px dashed ${C.astraHi}`, opacity: zoom}} />
					<div style={{position: 'absolute', left: xS - 110, top: base - hA, width: 6, height: hA - hS, background: '#fff', opacity: zoom}} />
					<div style={{position: 'absolute', left: 960, top: base - hA - 34, transform: 'translateX(-50%)', opacity: kf(f, [tGap + 18, tGap + 30], [0, 1]), padding: '3px 9px', borderRadius: 6, background: '#fff', color: '#0A0F1C', fontFamily: DISPLAY, fontWeight: 900, fontSize: 17, whiteSpace: 'nowrap'}}>
						0.4 points
					</div>
					<div style={{position: 'absolute', left: xA - 40, top: base - hA + 12, opacity: zoom, fontFamily: DISPLAY, fontWeight: 800, fontSize: 15, color: '#fff'}}>44.2</div>
					<div style={{position: 'absolute', left: xS - 40, top: base - hS + 12, opacity: zoom, fontFamily: DISPLAY, fontWeight: 800, fontSize: 15, color: '#fff'}}>43.8</div>
				</Camera>
				<Abs x={64} y={140} style={{opacity: appear(f, tAS)}}><ReportedTag extra="FrontierCode 2.0 · max effort · score" /></Abs>
			</AbsoluteFill>
			{/* D: cost per task */}
			<AbsoluteFill style={{opacity: life(f, tBill - 4, tSrc - 2, 8, 10)}}>
				<Camera f={f} keys={[[tBill, {s: 1.06, x: 980}], [tFifth, {s: 1, x: 960}], [tSrc, {s: 0.98, x: 960}]]}>
					<Abs x={960} y={262} center style={{fontFamily: DISPLAY, fontSize: 66, fontWeight: 800, opacity: appear(f, tBill)}}>Cost per task</Abs>
					{(['astra', 'sol'] as const).map((m, i) => {
						const at = m === 'astra' ? word('astracost', '$5') : word('solcost', '$1');
						const v = m === 'astra' ? 5.97 : 1.29, col = m === 'astra' ? C.astra : C.sol;
						const W = 1100 * (v / 5.97);
						return (
							<div key={m} style={{position: 'absolute', left: 420, top: 340 + i * 200, opacity: appear(f, at - 12)}}>
								<Badge m={m} size={40} style={{position: 'absolute', left: -20, top: 22, transform: 'translateX(-100%)'}} />
								<div style={{width: W * kf(f, [at - 6, at + 22], [0, 1]), height: 96, borderRadius: 16, background: `linear-gradient(90deg, ${col}, ${m === 'astra' ? C.astraHi : C.solHi})`, boxShadow: `0 0 40px ${col}44`}} />
								<div style={{position: 'absolute', left: W * kf(f, [at - 6, at + 22], [0, 1]) + 26, top: 4, fontFamily: DISPLAY, fontWeight: 900, fontSize: 76, color: col, whiteSpace: 'nowrap'}}>
									<Count f={f} a={at - 6} b={at + 22} to={v} dec={2} pre="$" />
								</div>
							</div>
						);
					})}
					{/* how many Sol tasks fit in one Astra task */}
					<div style={{position: 'absolute', left: 420, top: 740, display: 'flex', gap: 6, opacity: appear(f, tFifth - 6)}}>
						{Array.from({length: 5}).map((_, i) => {
							const p = pop(f, tFifth - 4 + i * 4);
							const w = i < 4 ? 1100 * (1.29 / 5.97) - 5 : 1100 * ((5.97 - 4 * 1.29) / 5.97) - 5;
							return <div key={i} style={{width: w, height: 60, borderRadius: 10, background: i < 4 ? C.sol : `repeating-linear-gradient(45deg, ${C.sol}66 0 8px, transparent 8px 16px)`, transform: `scaleY(${p})`, opacity: p}} />;
						})}
					</div>
					<div style={{position: 'absolute', left: 420, top: 820, fontFamily: FONT, fontSize: 28, color: C.ink, opacity: appear(f, tFifth + 6)}}>
						≈ 4.6 Sol tasks for the cost of one Astra task — <span style={{color: C.sol, fontWeight: 700}}>about a fifth</span>
					</div>
				</Camera>
				<Abs x={64} y={140} style={{opacity: appear(f, tBill + 4)}}><ReportedTag extra="cost per task on FrontierCode 2.0 · max" /></Abs>
			</AbsoluteFill>
			{/* E: source excerpt */}
			<AbsoluteFill style={{opacity: life(f, tSrc - 4, tCav - 2, 8, 10)}}>
				<Camera f={f} keys={[[tSrc, {s: 0.92, rx: 14, y: 560}], [tQuote, {s: 1.0, rx: 6, y: 540}], [tCav, {s: 1.12, rx: 0, y: 560}]]}>
					<Abs x={960} y={540} center>
						<Panel style={{width: 1240, padding: 0, overflow: 'hidden', background: '#F5F7FB', color: '#0D1424'}}>
							<div style={{background: '#E4E8F0', padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 12}}>
								{['#FF6159', '#FFBD2E', '#28C941'].map((c) => <div key={c} style={{width: 16, height: 16, borderRadius: 16, background: c}} />)}
								<div style={{marginLeft: 20, padding: '8px 18px', borderRadius: 10, background: '#fff', fontFamily: MONO, fontSize: 22, color: '#4A5670'}}>openai.com/index/introducing-gpt-6-2-astra-sol</div>
							</div>
							<div style={{padding: '40px 64px 54px'}}>
								<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 52}}>Introducing GPT-6.2 Astra and Sol</div>
								{[0.92, 0.85, 0.6].map((w, i) => <div key={i} style={{height: 16, width: `${w * 100}%`, borderRadius: 8, background: '#D8DDE7', marginTop: i ? 16 : 34}} />)}
								<div style={{position: 'relative', marginTop: 30, fontFamily: FONT, fontSize: 40, lineHeight: 1.45, fontWeight: 500}}>
									<span style={{backgroundImage: `linear-gradient(90deg, ${C.sol}AA, ${C.sol}AA)`, backgroundRepeat: 'no-repeat', backgroundSize: `${kf(f, [tQuote, tQuote + 70], [0, 100])}% 100%`, boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone', padding: '2px 4px'}}>
										On FrontierCode 2.0, GPT-6.2 Sol comes within 0.5 points of GPT-6.2 Astra at about one-fifth the cost (both at max).
									</span>
								</div>
								{[0.88, 0.7].map((w, i) => <div key={i} style={{height: 16, width: `${w * 100}%`, borderRadius: 8, background: '#D8DDE7', marginTop: i ? 16 : 30}} />)}
							</div>
						</Panel>
					</Abs>
				</Camera>
				<Abs x={64} y={140} style={{opacity: appear(f, tSrc + 6)}}><ReportedTag extra="Claim as quoted in coverage of OpenAI's announcement" /></Abs>
			</AbsoluteFill>
			{/* F: caveats */}
			<AbsoluteFill style={{opacity: life(f, tCav - 4, tTake - 2, 8, 10)}}>
				<Abs x={960} y={220} center style={{fontFamily: DISPLAY, fontSize: 70, fontWeight: 800}}>Two caveats</Abs>
				{[{t: tC1, h: 'OpenAI-reported', b: 'Vendor numbers, from one benchmark'}, {t: tC2, h: 'Cost per task, on this test', b: 'Not a quote for your own workload'}].map((c, i) => {
					const p = pop(f, c.t);
					return (
						<Abs key={i} x={560 + i * 800} y={560} center style={{opacity: Math.min(1, p * 1.4), transform: `translate(-50%,-50%) translateY(${(1 - p) * 60}px) rotate(${(i ? 1 : -1) * 1.5}deg)`}}>
							<Panel style={{width: 680, padding: '44px 48px'}}>
								<div style={{fontFamily: DISPLAY, fontSize: 90, fontWeight: 900, color: C.faint, lineHeight: 1}}>{i + 1}</div>
								<div style={{fontFamily: DISPLAY, fontSize: 48, fontWeight: 800, marginTop: 16}}>{c.h}</div>
								<div style={{fontFamily: FONT, fontSize: 32, color: C.dim, marginTop: 12}}>{c.b}</div>
							</Panel>
						</Abs>
					);
				})}
			</AbsoluteFill>
			{/* G: what it tells you, and where the gap shows up */}
			<AbsoluteFill style={{opacity: life(f, tTake - 4, 1e9, 8)}}>
				<Camera f={f} keys={[[tTake, {s: 1.04}], [tWhere, {s: 1}], [tWhere + 50, {s: 1.06, y: 560}]]}>
					<Abs x={960} y={kf(f, [tWhere - 4, tWhere + 14], [420, 210])} center style={{textAlign: 'center', whiteSpace: 'nowrap', transform: `translate(-50%,-50%) scale(${kf(f, [tWhere - 4, tWhere + 14], [1, 0.62])})`}}>
						<div style={{fontFamily: FONT, fontSize: 32, color: C.dim, letterSpacing: 3, fontWeight: 700}}>ON WELL-DEFINED CODING CHANGES</div>
						<div style={{fontFamily: DISPLAY, fontSize: 92, fontWeight: 900, marginTop: 10, opacity: appear(f, tTake2)}}>
							The flagship isn't <span style={{color: C.sol}}>buying you much</span>
						</div>
					</Abs>
					<Abs x={960} y={420} center style={{fontFamily: DISPLAY, fontSize: 70, fontWeight: 800, whiteSpace: 'nowrap', opacity: appear(f, tWhere), transform: `translate(-50%,-50%) translateY(${(1 - appear(f, tWhere, 16)) * 30}px)`}}>
						So where does the gap show up?
					</Abs>
					{['A website', 'A hard bug', 'A slide deck'].map((t, i) => {
						const p = pop(f, tWhere + 10 + i * 6);
						return (
							<Abs key={t} x={520 + i * 440} y={660} center style={{opacity: Math.min(1, p * 1.4), transform: `translate(-50%,-50%) scale(${0.6 + 0.4 * p})`}}>
								<Panel style={{width: 380, height: 220, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16}}>
									<div style={{fontFamily: MONO, fontSize: 30, color: C.dim}}>0{i + 1}</div>
									<div style={{fontFamily: DISPLAY, fontSize: 44, fontWeight: 800}}>{t}</div>
								</Panel>
							</Abs>
						);
					})}
				</Camera>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
void ModelGlyph; void wordAfter;
