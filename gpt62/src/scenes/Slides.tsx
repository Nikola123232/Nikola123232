import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Badge, C, Camera, DISPLAY, FONT, MONO, Pick, Tag, appear, cue, kf, life, pop, rnd, word, easeInOut} from '../lib';

const BRAND = '#0F3D3E', BRAND2 = '#2BB3A3';
const HEAD = ['Q3 at a glance', 'Churn is down', 'Three new regions', 'Revenue by month', 'Pricing test', 'What worked', 'Risks', 'Hiring plan', 'Next quarter', 'Asks'];

const Slide: React.FC<{i: number; brand: number; footer: number; notes: number; bad?: boolean}> = ({i, brand, footer, notes, bad}) => (
	<div style={{width: 320, height: 180, borderRadius: 10, overflow: 'hidden', position: 'relative', background: brand > 0.5 ? '#FFFFFF' : '#FBFAF7', boxShadow: '0 18px 40px rgba(0,0,0,0.45)', border: brand > 0.5 ? `3px solid ${BRAND2}` : '3px solid transparent'}}>
		<div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: 10 * brand, background: BRAND2}} />
		<div style={{padding: '16px 20px', fontFamily: brand > 0.5 ? DISPLAY : FONT, fontWeight: 800, fontSize: 22, color: brand > 0.5 ? BRAND : '#222'}}>{HEAD[i]}</div>
		{i === 3 ? (
			<div style={{display: 'flex', gap: 6, alignItems: 'flex-end', height: 70, margin: '0 20px'}}>
				{[30, 42, 38, 55, 61, 70].map((h, k) => <div key={k} style={{width: 26, height: h, background: brand > 0.5 ? BRAND2 : '#A8A29A', borderRadius: 3}} />)}
			</div>
		) : i === 1 ? (
			<div style={{margin: '0 20px', fontFamily: DISPLAY, fontWeight: 900, fontSize: 44, color: bad ? C.red : brand > 0.5 ? BRAND : '#333'}}>{bad ? '18.4%' : '14.8%'}<span style={{fontSize: 16, fontWeight: 600, marginLeft: 8}}>retention lift</span></div>
		) : (
			[0.8, 0.6, 0.7].map((w, k) => <div key={k} style={{height: 9, width: `${w * 80}%`, marginLeft: 20, marginBottom: 9, borderRadius: 5, background: '#D5D1CA'}} />)
		)}
		<div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 22 * footer, background: BRAND, color: '#CFE9E5', fontFamily: FONT, fontSize: 10, display: 'flex', alignItems: 'center', paddingLeft: 14, overflow: 'hidden'}}>Confidential · © Example Corp · Not investment advice</div>
		<div style={{position: 'absolute', right: 8, top: 8, padding: '2px 8px', borderRadius: 6, background: '#FFE58A', fontFamily: FONT, fontSize: 11, fontWeight: 700, color: '#3a2c00', opacity: notes}}>notes</div>
	</div>
);

export const Slides: React.FC<{f: number}> = ({f}) => {
	const S0 = cue('slides'), tTen = word('slides', 'ten'), tTom = word('slides', 'tomorrow'), tFrag = cue('frag');
	const tSol = cue('slidesol'), tOut = cue('outline'), tHead = word('outline', 'headlines'), tSpk = word('outline', 'speaker');
	const tComp = cue('slidecomp'), tTpl = cue('template'), tFonts = word('template', 'fixed'), tLay = word('template', 'locked'), tFoot = word('template', 'legal');
	const tSrc = cue('source2'), tRep = word('source2', 'forty'), tSheet = word('source2', 'spreadsheet'), tMatch = word('source2', 'match');
	const tWrong = cue('wrongnum'), tPick = cue('slidepick'), tStakes = cue('stakes');
	const toDeck = kf(f, [tSol - 10, tSol + 20], [0, 1], easeInOut);
	const brand = kf(f, [tFonts, tFonts + 14], [0, 1]), footer = kf(f, [tFoot, tFoot + 14], [0, 1]);
	const notesOn = kf(f, [tSpk, tSpk + 10], [0, 1]);
	const flash = kf(f, [tComp, tComp + 3, tComp + 12], [0, 0.7, 0]);
	const stakesP = appear(f, tStakes - 4, 16);
	const NOTES = ['Q3 churn ↓ ~2 pts?', '3 new regions!!', 'chart: rev by month??', 'pricing test → results', 'hire 2 eng', 'risks: supply?'];
	return (
		<AbsoluteFill style={{background: 'radial-gradient(1200px 800px at 50% 35%, #2A2233, #120F17)'}}>
			{/* desk texture */}
			<AbsoluteFill style={{backgroundImage: 'repeating-linear-gradient(115deg, rgba(255,255,255,0.018) 0 2px, transparent 2px 14px)'}} />
			<Camera f={f} keys={[[S0, {s: 1.06, y: 540}], [tSol - 10, {s: 1.0}], [tOut, {s: 0.96, rx: 0}], [tComp, {s: 1.02}], [tTpl + 20, {s: 0.94}], [tSrc, {s: 0.9, x: 900}], [tWrong - 6, {s: 0.9, x: 900}], [tWrong + 20, {s: 2.7, x: 1020, y: 430}], [tPick - 6, {s: 2.7, x: 1020, y: 430}], [tPick + 12, {s: 0.95, x: 960}]]}>
				{/* sticky notes -> deck */}
				{NOTES.map((t, i) => {
					const p = pop(f, (i < 2 ? S0 + 10 + i * 8 : tFrag + (i - 2) * 9));
					const x0 = 480 + (i % 3) * 470 + rnd(i) * 60, y0 = 380 + Math.floor(i / 3) * 320 + rnd(i + 4) * 40;
					const fly = kf(f, [tSol - 10 + i * 2, tSol + 14 + i * 2], [0, 1], easeInOut);
					return (
						<Abs key={i} x={x0 + (960 - x0) * fly} y={y0 + (540 - y0) * fly} center style={{opacity: Math.min(1, p) * (1 - fly), transform: `translate(-50%,-50%) rotate(${(rnd(i + 2) - 0.5) * 12}deg) scale(${(0.5 + 0.5 * p) * (1 - fly * 0.7)})`}}>
							<div style={{width: 330, height: 230, padding: 24, boxSizing: 'border-box', background: ['#FFE58A', '#FFC7A8', '#B8F0D8'][i % 3], boxShadow: '0 20px 40px rgba(0,0,0,0.5)', fontFamily: "'Inter'", fontStyle: 'italic', fontWeight: 600, fontSize: 36, color: '#2A2318', lineHeight: 1.2}}>{t}</div>
						</Abs>
					);
				})}
				<Abs x={1600} y={140} center style={{opacity: life(f, tTom - 4, tSol), transform: `translate(-50%,-50%) rotate(4deg) scale(${pop(f, tTom - 4)})`}}>
					<div style={{padding: '14px 24px', borderRadius: 12, background: C.red, color: '#fff', fontFamily: FONT, fontWeight: 800, fontSize: 30}}>Due tomorrow, 9:00</div>
				</Abs>
				<Abs x={960} y={150} center style={{opacity: life(f, tTen - 4, tSol), fontFamily: DISPLAY, fontWeight: 900, fontSize: 48, color: '#fff', whiteSpace: 'nowrap'}}>Need: a 10-slide deck</Abs>
				{/* deck grid in 3D */}
				<Abs x={960} y={kf(f, [tSrc - 6, tSrc + 14], [540, 520])} center style={{opacity: toDeck, transformStyle: 'preserve-3d', transform: `translate(-50%,-50%) translateX(${kf(f, [tSrc - 6, tSrc + 14], [0, 270])}px) scale(${kf(f, [tSrc - 6, tSrc + 14], [0.9, 0.64])}) perspective(2000px) rotateX(${kf(f, [tSol, tSol + 30], [40, 18])}deg) rotateZ(${kf(f, [tSol, tSol + 30], [-8, 0])}deg)`}}>
					<div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 320px)', gap: 26}}>
						{Array.from({length: 10}).map((_, i) => {
							const p = pop(f, tSol + 4 + i * 3);
							const lift = i === 1 ? kf(f, [tWrong - 4, tWrong + 12], [0, 1]) : 0;
							return (
								<div key={i} style={{transform: `scale(${p}) translateZ(${lift * 80}px)`, outline: f > tHead && f < tSpk + 20 && i < 10 ? `3px solid ${C.sol}66` : 'none', borderRadius: 10}}>
									<Slide i={i} brand={brand} footer={footer} notes={notesOn} bad={i === 1 && f > tWrong + 6} />
								</div>
							);
						})}
					</div>
				</Abs>
				{/* Sol is fine tag */}
				<Abs x={960} y={150} center style={{opacity: life(f, tSol + 4, tComp, 10, 6)}}>
					<div style={{display: 'flex', gap: 18, alignItems: 'center'}}>
						<Tag color={C.ink} size={26}>Internal update</Tag>
						<span style={{fontFamily: DISPLAY, fontSize: 40, color: C.ink}}>→</span>
						<Badge m="sol" size={44} />
						<span style={{fontFamily: DISPLAY, fontSize: 40, fontWeight: 800, color: C.ink}}>is fine</span>
					</div>
				</Abs>
				<Abs x={960} y={880} center style={{opacity: life(f, tOut + 4, tComp, 10, 6), display: 'flex', gap: 16}}>
					{[['Outline', tOut + 6], ['Headlines', tHead], ['Speaker notes', tSpk]].map(([t, at]) => <div key={t as string} style={{opacity: appear(f, at as number)}}><Tag color={C.sol} size={24}>{t as string}</Tag></div>)}
				</Abs>
				{/* template constraints */}
				<Abs x={960} y={160} center style={{opacity: life(f, tComp, tSrc - 2, 6, 10), whiteSpace: 'nowrap', fontFamily: DISPLAY, fontWeight: 900, fontSize: 64, color: '#fff'}}>
					{f < tTpl ? 'Now change the job.' : 'Strict brand template'}
				</Abs>
				<Abs x={960} y={890} center style={{opacity: life(f, tFonts - 4, tSrc - 2, 8, 10), display: 'flex', gap: 18}}>
					{[['Fixed fonts', tFonts], ['Locked layouts', tLay], ['Legal footer, every slide', tFoot]].map(([t, at]) => (
						<div key={t as string} style={{opacity: appear(f, at as number), transform: `scale(${0.7 + 0.3 * pop(f, at as number)})`, padding: '14px 22px', borderRadius: 14, background: BRAND, color: '#DFF6F2', fontFamily: FONT, fontWeight: 700, fontSize: 28, display: 'flex', alignItems: 'center', gap: 12}}><svg width={22} height={26} viewBox="0 0 22 26"><rect x={1} y={11} width={20} height={14} rx={3} fill="#DFF6F2" /><path d="M5,11 V7 a6,6 0 0 1 12,0 V11" fill="none" stroke="#DFF6F2" strokeWidth={3} /></svg>{t as string}</div>
					))}
				</Abs>
				{/* sources */}
				<Abs x={330} y={380} center style={{opacity: life(f, tRep - 4, tPick, 10, 10)}}>
					{Array.from({length: 6}).map((_, k) => (
						<div key={k} style={{position: 'absolute', left: -150 + k * 7, top: -190 + k * 7, width: 300, height: 380, background: k === 5 ? '#fff' : '#E8E4DC', borderRadius: 6, boxShadow: '0 6px 16px rgba(0,0,0,0.35)'}}>
							{k === 5 && <div style={{padding: 24, fontFamily: FONT, color: '#222'}}>
								<div style={{fontWeight: 800, fontSize: 24}}>Q3 Report</div>
								<div style={{fontSize: 18, color: '#777', marginTop: 4}}>40 pages</div>
								{Array.from({length: 9}).map((_, r) => <div key={r} style={{height: 8, width: `${60 + rnd(r) * 35}%`, background: '#DDD', borderRadius: 4, marginTop: 14}} />)}
								<div style={{marginTop: 14, fontWeight: 800, fontSize: 22, color: BRAND, background: '#E2F5F2', display: 'inline-block', padding: '2px 8px'}}>retention lift 14.8%</div>
							</div>}
						</div>
					))}
				</Abs>
				<Abs x={330} y={780} center style={{opacity: life(f, tSheet - 4, tPick, 10, 10)}}>
					<div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 76px)', gap: 3, padding: 8, background: '#1E6B45', borderRadius: 8}}>
						{Array.from({length: 16}).map((_, k) => <div key={k} style={{height: 34, background: k < 4 ? '#CDEBD9' : '#fff', fontFamily: MONO, fontSize: 14, color: '#234', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{k < 4 ? ['Q', 'Rev', 'Churn', 'Ret'][k] : (rnd(k) * 90 + 10).toFixed(1)}</div>)}
					</div>
				</Abs>
				<svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, opacity: life(f, tMatch - 6, tWrong, 8, 8), overflow: 'visible'}}>
					{[[480, 420, 1000, 360], [480, 780, 1300, 560], [480, 780, 900, 560]].map(([x1, y1, x2, y2], k) => (
						<path key={k} d={`M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`} fill="none" stroke={BRAND2} strokeWidth={4} strokeDasharray={900} strokeDashoffset={900 * (1 - kf(f, [tMatch - 6 + k * 4, tMatch + 14 + k * 4], [0, 1]))} />
					))}
				</svg>
				<Abs x={1220} y={170} center style={{opacity: life(f, tMatch, tWrong, 8, 8), fontFamily: DISPLAY, fontWeight: 800, fontSize: 44, color: BRAND2, whiteSpace: 'nowrap'}}>Every figure has to match</Abs>
				{/* wrong number callout (world coords near slide 2) */}
				<Abs x={1020} y={360} center style={{opacity: life(f, tWrong + 10, tPick + 4, 8, 8), whiteSpace: 'nowrap', transform: 'translate(-50%,-50%) scale(0.4)'}}>
					<div style={{padding: '14px 26px', borderRadius: 14, background: C.red, color: '#fff', fontFamily: DISPLAY, fontWeight: 900, fontSize: 44}}>Slide says 18.4% · report says 14.8%</div>
					<div style={{marginTop: 10, textAlign: 'center'}}><Tag color="#fff" size={26} style={{background: 'rgba(0,0,0,0.6)'}}>Client-facing</Tag></div>
				</Abs>
			</Camera>
			<AbsoluteFill style={{background: '#fff', opacity: flash}} />
			<AbsoluteFill style={{background: `rgba(0,0,0,${kf(f, [tPick - 4, tPick + 10], [0, 0.55]) + kf(f, [tStakes - 6, tStakes + 8], [0, 0.25])})`}} />
			<Pick f={f} at={tPick} m="astra" reason="Strict template, complex sources, one number that can't be wrong." y={kf(f, [tStakes - 6, tStakes + 10], [520, 250])} scale={kf(f, [tStakes - 6, tStakes + 10], [1, 0.72])} />
			{/* same task, different stakes */}
			<Abs x={960} y={640} center style={{opacity: stakesP, transform: `translate(-50%,-50%) translateY(${(1 - stakesP) * 40}px)`, display: 'flex', gap: 40}}>
				{([['Internal update', 'sol'], ['Client deck, strict template', 'astra']] as const).map(([t, m]) => (
					<div key={t} style={{width: 560, padding: '28px 34px', borderRadius: 20, background: 'rgba(12,14,22,0.9)', border: `2px solid ${m === 'sol' ? C.sol : C.astra}`}}>
						<div style={{fontFamily: FONT, fontSize: 24, color: C.dim, letterSpacing: 2, fontWeight: 700}}>SAME TASK</div>
						<div style={{fontFamily: DISPLAY, fontSize: 38, fontWeight: 800, margin: '8px 0 16px', whiteSpace: 'nowrap'}}>{t}</div>
						<Badge m={m} size={46} />
					</div>
				))}
			</Abs>
		</AbsoluteFill>
	);
};
