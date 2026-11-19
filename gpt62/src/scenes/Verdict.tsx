import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Badge, C, Camera, DISPLAY, FONT, ModelGlyph, Panel, Tag, appear, cue, kf, life, pop, word, wordAfter, TOTAL_FRAMES, cueEnd, easeInOut} from '../lib';

const Task: React.FC<{f: number; at: number; t: string; m: 'astra' | 'sol'}> = ({f, at, t, m}) => {
	const p = pop(f, at);
	const col = m === 'astra' ? C.astra : C.sol;
	return (
		<div style={{opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * -50}px) rotate(${(1 - p) * (m === 'sol' ? -4 : 4)}deg)`, marginBottom: 18, padding: '24px 30px', borderRadius: 18,
			background: 'rgba(14,20,34,0.95)', borderLeft: `8px solid ${col}`, fontFamily: FONT, fontWeight: 600, fontSize: 36, color: C.ink, boxShadow: '0 16px 40px rgba(0,0,0,0.4)'}}>{t}</div>
	);
};

export const Verdict: React.FC<{f: number}> = ({f}) => {
	const V0 = cue('verdict'), tSol = cue('vsol'), tAst = cue('vastra'), tRule = cue('rule'), tR1 = cue('r1'), tR2 = cue('r2'), tR3 = cue('r3'), tEnd = cue('end');
	const tFrac = wordAfter('fraction', tSol);
	const sTasks = [word('vsol', 'bakery'), word('vsol', 'internal'), word('vsol', 'routine')];
	const aTasks = [word('vastra', 'cross'), word('vastra', 'client')];
	const gates = [word('r2', 'connected'), word('r2', 'check'), word('r2', 'mistake')];
	const toRule = kf(f, [tRule - 6, tRule + 14], [0, 1], easeInOut);
	const toEnd = kf(f, [tEnd - 8, tEnd + 10], [0, 1], easeInOut);
	const tAstraWord = word('end', 'astra');
	const stay = appear(f, tR3, 12);
	return (
		<AbsoluteFill>
			{/* columns */}
			<AbsoluteFill style={{opacity: 1 - toRule, transform: `translateY(${toRule * -80}px)`}}>
				<Camera f={f} keys={[[V0, {s: 1.06}], [tAst - 10, {s: 1.0, x: 900}], [tAst + 30, {s: 1.0, x: 1020}], [tRule, {s: 1.0, x: 960}]]}>
					<Abs x={960} y={160} center style={{fontFamily: DISPLAY, fontSize: 76, fontWeight: 900, opacity: appear(f, V0)}}>The verdict</Abs>
					{(['sol', 'astra'] as const).map((m, i) => (
						<Abs key={m} x={i ? 1010 : 150} y={270} w={760} style={{opacity: appear(f, i ? tAst - 8 : tSol - 8)}}>
							<div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 18, marginBottom: 26, borderBottom: `3px solid ${m === 'sol' ? C.sol : C.astra}`}}>
								<Badge m={m} size={64} />
								<span style={{fontFamily: FONT, fontSize: 26, color: C.dim, letterSpacing: 2, fontWeight: 700}}>{m === 'sol' ? 'THE DEFAULT' : 'THE ESCALATION'}</span>
							</div>
							{m === 'sol'
								? ['Bakery landing page', 'Internal update deck', 'Routine code changes'].map((t, k) => <Task key={t} f={f} at={sTasks[k]} t={t} m="sol" />)
								: ['Cross-file checkout bug', 'Client deck, strict template'].map((t, k) => <Task key={t} f={f} at={aTasks[k]} t={t} m="astra" />)}
							{m === 'sol' && (
								<div style={{marginTop: 8, opacity: appear(f, tFrac - 20)}}>
									<Tag color={C.sol} size={20}>Within 0.5 pts · ~⅕ the cost per task · OpenAI-reported</Tag>
								</div>
							)}
						</Abs>
					))}
				</Camera>
			</AbsoluteFill>
			{/* switch rule */}
			<AbsoluteFill style={{opacity: toRule * (1 - toEnd)}}>
				<Abs x={960} y={170} center style={{fontFamily: DISPLAY, fontSize: 70, fontWeight: 900, whiteSpace: 'nowrap'}}>The switch rule</Abs>
				<Abs x={300} y={520} center style={{opacity: appear(f, tR1 - 4), transform: `translate(-50%,-50%) scale(${0.8 + 0.2 * pop(f, tR1 - 4)})`}}>
					<Panel glow={C.sol} style={{padding: '30px 40px', textAlign: 'center'}}>
						<div style={{fontFamily: FONT, fontSize: 24, color: C.dim, letterSpacing: 2, fontWeight: 700}}>START WITH</div>
						<Badge m="sol" size={64} />
					</Panel>
				</Abs>
				{['Many connected pieces', "Can't check it quickly", 'A mistake costs more than the price gap'].map((t, k) => {
					const on = appear(f, gates[k] - 2, 10);
					return (
						<Abs key={t} x={960} y={360 + k * 160} center style={{opacity: 0.25 + 0.75 * on, transform: `translate(-50%,-50%) scale(${0.92 + 0.08 * on})`}}>
							<div style={{width: 720, padding: '22px 28px', borderRadius: 16, background: 'rgba(14,20,34,0.95)', border: `2px solid ${on > 0.5 ? C.astra : C.line}`, fontFamily: FONT, fontWeight: 700, fontSize: 32, color: C.ink, textAlign: 'center', whiteSpace: 'nowrap'}}>{t}</div>
						</Abs>
					);
				})}
				<svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
					{[0, 1, 2].map((k) => {
						const p = kf(f, [gates[k] - 2, gates[k] + 14], [0, 1]);
						const y = 360 + k * 160;
						return (
							<g key={k}>
								<path d={`M420,520 C520,520 500,${y} 600,${y}`} fill="none" stroke={C.sol} strokeWidth={4} strokeOpacity={0.6} strokeDasharray={400} strokeDashoffset={400 * (1 - p)} />
								<path d={`M1320,${y} C1400,${y} 1420,520 1500,520`} fill="none" stroke={C.astra} strokeWidth={4} strokeOpacity={0.8} strokeDasharray={400} strokeDashoffset={400 * (1 - p)} />
							</g>
						);
					})}
					<path d="M300,610 C300,860 960,880 960,880" fill="none" stroke={C.sol} strokeWidth={4} strokeDasharray="10 10" opacity={stay} />
				</svg>
				<Abs x={1640} y={520} center style={{opacity: appear(f, gates[0] + 6), transform: `translate(-50%,-50%) scale(${0.8 + 0.2 * pop(f, gates[0] + 6)})`}}>
					<Panel glow={C.astra} style={{padding: '30px 40px', textAlign: 'center'}}>
						<div style={{fontFamily: FONT, fontSize: 24, color: C.dim, letterSpacing: 2, fontWeight: 700}}>ANY TRUE? SWITCH TO</div>
						<Badge m="astra" size={64} />
					</Panel>
				</Abs>
				<Abs x={960} y={870} center style={{opacity: stay, padding: '14px 26px', borderRadius: 14, background: 'rgba(40,24,4,0.92)', border: `2px solid ${C.sol}`, fontFamily: FONT, fontWeight: 700, fontSize: 30, color: C.solHi, whiteSpace: 'nowrap'}}>
					None true? Sol is probably enough.
				</Abs>
			</AbsoluteFill>
			{/* final line */}
			<AbsoluteFill style={{opacity: toEnd}}>
				<Abs x={560} y={430} center style={{opacity: appear(f, tEnd)}}><ModelGlyph m="sol" size={220} spin={f * 0.3} /></Abs>
				<Abs x={1360} y={430} center style={{opacity: appear(f, tAstraWord)}}><ModelGlyph m="astra" size={220} spin={-f * 0.3} /></Abs>
				<Abs x={560} y={640} center style={{textAlign: 'center', opacity: appear(f, tEnd), whiteSpace: 'nowrap'}}>
					<div style={{fontFamily: DISPLAY, fontSize: 92, fontWeight: 900, color: C.sol}}>Sol</div>
					<div style={{fontFamily: DISPLAY, fontSize: 52, fontWeight: 800, color: C.ink}}>is your default.</div>
				</Abs>
				<Abs x={1360} y={640} center style={{textAlign: 'center', opacity: appear(f, tAstraWord), whiteSpace: 'nowrap'}}>
					<div style={{fontFamily: DISPLAY, fontSize: 92, fontWeight: 900, color: C.astra}}>Astra</div>
					<div style={{fontFamily: DISPLAY, fontSize: 52, fontWeight: 800, color: C.ink}}>is your escalation.</div>
				</Abs>
				<div style={{position: 'absolute', left: 960, top: 300, width: 4, height: 460, background: `linear-gradient(${C.astra}, #fff, ${C.sol})`, transform: `scaleY(${kf(f, [tEnd, tEnd + 20], [0, 1])}) rotate(4deg)`, opacity: 0.8}} />
				<Abs x={960} y={880} center style={{opacity: life(f, cueEnd('end'), TOTAL_FRAMES, 12, 1), whiteSpace: 'nowrap', fontFamily: FONT, fontSize: 24, color: C.dim, letterSpacing: 1}}>
					Benchmark figures: OpenAI-reported · FrontierCode 2.0 · max effort · cost per task on that test
				</Abs>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
