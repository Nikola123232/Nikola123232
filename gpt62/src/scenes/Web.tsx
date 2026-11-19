import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, C, Camera, DISPLAY, FONT, MONO, Pick, Tag, appear, cue, kf, life, pop, word, wordAfter, easeInOut} from '../lib';

const INK = '#2B1D12', CREAM = '#FFF8EE', CRUST = '#C7792E', PAPER = '#ECE5D8';

const Box: React.FC<{x: number; y: number; w: number; h: number; draw: number; fill: number; label: string; children?: React.ReactNode; red?: number; dx?: number}> = ({x, y, w, h, draw, fill, label, children, red = 0, dx = 0}) => (
	<div style={{position: 'absolute', left: x + dx, top: y, width: w, height: h, opacity: draw > 0 ? 1 : 0}}>
		<svg width={w} height={h} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
			<rect x={2} y={2} width={w - 4} height={h - 4} rx={14} fill="none" stroke={red > 0 ? C.red : '#7A8AA6'} strokeWidth={red > 0 ? 5 : 3} strokeDasharray={`${(w + h) * 2 * draw} 4000`} style={{strokeDasharray: red > 0 ? undefined : `${(w + h) * 2 * draw} 4000`}} />
		</svg>
		<div style={{position: 'absolute', inset: 0, borderRadius: 14, overflow: 'hidden', opacity: fill}}>{children}</div>
		<div style={{position: 'absolute', left: 16, top: 12, fontFamily: MONO, fontSize: 20, color: '#5B6B88', opacity: (1 - fill) * draw}}>{label}</div>
	</div>
);

const Croissant: React.FC<{size: number}> = ({size}) => (
	<svg width={size} height={size * 0.6} viewBox="0 0 200 120">
		{[[-70, 36], [-35, 48], [0, 56], [35, 48], [70, 36]].map(([dx, r], i) => (
			<ellipse key={i} cx={100 + dx} cy={70 - (i === 2 ? 8 : 0)} rx={r * 0.62} ry={r * 0.8} fill={i % 2 ? '#E0A055' : CRUST} stroke="#8A4B16" strokeWidth={3} transform={`rotate(${dx * 0.5} ${100 + dx} 70)`} />
		))}
	</svg>
);

/** The bakery page, desktop layout. All content is invented for the illustration. */
const Site: React.FC<{f: number; tParts: number[]; fill: number; round: number; broken: number; formState: number}> = ({f, tParts, fill, round, broken, formState}) => {
	const d = (i: number) => kf(f, [tParts[i], tParts[i] + 16], [0, 1]);
	return (
		<div style={{position: 'relative', width: 1240, height: 700, background: fill > 0.5 ? CREAM : '#F7F8FB'}}>
			{/* nav */}
			<div style={{position: 'absolute', left: 40, top: 22, fontFamily: DISPLAY, fontWeight: 900, fontSize: round >= 1 ? 40 : 30, color: INK, opacity: fill}}>Crumb &amp; Co.</div>
			<Box x={40} y={80} w={1160} h={250} draw={d(0)} fill={fill} label="hero image" dx={broken * 140} red={broken}>
				<div style={{position: 'absolute', inset: 0, background: `linear-gradient(120deg, #F3C98B, #E59A4C)`, display: 'flex', alignItems: 'center', padding: '0 60px', gap: 50}}>
					<div>
						<div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 64, color: INK, lineHeight: 1.05}}>Baked before<br />sunrise.</div>
						<div style={{marginTop: 16, display: 'inline-block', padding: '10px 22px', borderRadius: 30, background: INK, color: CREAM, fontFamily: FONT, fontWeight: 700, fontSize: 22}}>Order for pickup</div>
					</div>
					<div style={{marginLeft: 'auto'}}><Croissant size={330} /></div>
				</div>
			</Box>
			<Box x={40} y={350} w={560} h={320} draw={d(1)} fill={fill} label="menu">
				<div style={{padding: '22px 28px', background: '#fff', height: '100%', boxSizing: 'border-box', fontFamily: FONT, color: INK}}>
					<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 32, marginBottom: 10}}>Menu</div>
					{[['Butter croissant', '3.50'], ['Sourdough loaf', '7.00'], ['Cardamom bun', '4.25'], ...(round >= 2 ? [['Gluten-free brownie', '4.00']] : [])].map(([n, p]) => (
						<div key={n} style={{display: 'flex', justifyContent: 'space-between', fontSize: 25, padding: '8px 0', borderBottom: '1.5px dashed #E6D8C4'}}><span>{n}</span><span>{p}</span></div>
					))}
				</div>
			</Box>
			<Box x={620} y={350} w={280} h={320} draw={d(2)} fill={fill} label="hours">
				<div style={{padding: '22px 24px', background: '#FBEBD3', height: '100%', boxSizing: 'border-box', fontFamily: FONT, color: INK, fontSize: 23, lineHeight: 1.7}}>
					<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 30, marginBottom: 6}}>Hours</div>
					Mon–Fri 7–4<br />Sat 8–2<br /><span style={{color: round >= 3 ? CRUST : '#A08E78', fontWeight: round >= 3 ? 800 : 400}}>{round >= 3 ? 'Sun 8–12' : 'Sun closed'}</span>
				</div>
			</Box>
			<Box x={920} y={350} w={280} h={320} draw={d(3)} fill={fill} label="contact form">
				<div style={{padding: '22px 22px', background: '#fff', height: '100%', boxSizing: 'border-box', fontFamily: FONT, color: INK}}>
					<div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: 30, marginBottom: 12}}>Say hi</div>
					{['Name', 'Email', 'Message'].map((n) => <div key={n} style={{height: n === 'Message' ? 70 : 40, borderRadius: 8, border: '2px solid #E6D8C4', marginBottom: 10, fontSize: 18, color: '#A08E78', padding: '8px 10px', boxSizing: 'border-box'}}>{n}</div>)}
					<div style={{height: 44, borderRadius: 10, background: formState < 0 ? C.red : formState > 0 ? '#2E9D6A' : INK, color: '#fff', fontWeight: 700, fontSize: 20, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
						{formState < 0 ? '✕ Send failed' : formState > 0 ? '✓ Sent' : 'Send'}
					</div>
				</div>
			</Box>
		</div>
	);
};

const Browser: React.FC<{children: React.ReactNode; url?: string}> = ({children, url = 'crumbandco.example'}) => (
	<div style={{borderRadius: 22, overflow: 'hidden', boxShadow: '0 50px 120px rgba(60,40,20,0.35), 0 0 0 2px rgba(0,0,0,0.06)', background: '#fff'}}>
		<div style={{height: 56, background: '#F1ECE4', display: 'flex', alignItems: 'center', gap: 10, padding: '0 22px'}}>
			{['#FF6159', '#FFBD2E', '#28C941'].map((c) => <div key={c} style={{width: 15, height: 15, borderRadius: 15, background: c}} />)}
			<div style={{marginLeft: 18, padding: '6px 18px', borderRadius: 10, background: '#fff', fontFamily: MONO, fontSize: 19, color: '#7C6A58'}}>{url}</div>
		</div>
		{children}
	</div>
);

const Phone: React.FC<{f: number; at: number}> = ({f, at}) => (
	<div style={{width: 300, height: 600, borderRadius: 46, background: '#1A1410', padding: 14, boxShadow: '0 40px 90px rgba(60,40,20,0.45)'}}>
		<div style={{width: '100%', height: '100%', borderRadius: 34, overflow: 'hidden', background: CREAM, fontFamily: FONT, color: INK}}>
			<div style={{padding: '30px 18px 10px', fontFamily: DISPLAY, fontWeight: 900, fontSize: 26}}>Crumb &amp; Co.</div>
			{[['linear-gradient(120deg,#F3C98B,#E59A4C)', 150, 'Baked before sunrise.'], ['#fff', 120, 'Menu'], ['#FBEBD3', 90, 'Hours'], ['#fff', 110, 'Say hi']].map(([bg, h, t], i) => {
				const p = kf(f, [at + i * 5, at + 14 + i * 5], [0, 1]);
				return <div key={i} style={{margin: '0 14px 10px', height: h as number, borderRadius: 12, background: bg as string, border: '1.5px solid #E6D8C4', transform: `translateY(${(1 - p) * 60}px)`, opacity: p, padding: 12, boxSizing: 'border-box', fontWeight: 800, fontSize: 19}}>{t}</div>;
			})}
		</div>
	</div>
);

export const Web: React.FC<{f: number}> = ({f}) => {
	const W0 = cue('web'), tParts = [word('webparts', 'hero'), word('webparts', 'menu'), word('webparts', 'opening'), word('webparts', 'contact')];
	const tWire = cue('wire'), tClear = word('wire', 'clear'), tFew = word('wire', 'few'), tEasy = word('wire', 'easy');
	const tComp = cue('webcomp'), tMob = cue('mobile'), tPh = word('mobile', 'phones'), tLoad = word('mobile', 'load'), tSend = word('mobile', 'send');
	const tRounds = cue('rounds'), tCheck = cue('webcheck'), tBreak = word('webcheck', 'breaks'), tFail = word('webcheck', 'fails'), tPick = cue('webpick'), tPass = cue('passes');
	const tMore = wordAfter('more', tRounds);
	const fill = kf(f, [tWire + 10, tWire + 40], [0, 1]);
	const roundsAt = [tRounds + 30, tRounds + 50, tRounds + 70];
	const round = roundsAt.filter((r) => f > r + 8).length;
	const broken = Math.max(0, kf(f, [tBreak, tBreak + 6], [0, 1]) - kf(f, [tBreak + 30, tBreak + 40], [0, 1]));
	const formState = f > tFail + 28 ? 1 : f > tFail ? -1 : 0;
	const side = kf(f, [tClear - 10, tClear + 10], [0, 1], easeInOut) * (1 - kf(f, [tComp - 6, tComp + 10], [0, 1]));
	const phone = kf(f, [tPh - 8, tPh + 14], [0, 1], easeInOut);
	const dimPick = kf(f, [tPick - 4, tPick + 10], [0, 1]);
	const browserX = 960 - side * 260 - phone * 190;
	return (
		<AbsoluteFill style={{background: PAPER}}>
			{/* dotted design canvas */}
			<AbsoluteFill style={{backgroundImage: 'radial-gradient(#C9BFAE 2px, transparent 2px)', backgroundSize: '36px 36px', backgroundPosition: `${-f * 0.4}px 0px`, opacity: 0.8}} />
			<Camera f={f} keys={[[W0, {s: 1.0, x: 960, y: 520, ry: -6}], [tParts[0], {s: 0.96, x: 960, y: 540, ry: 0}], [tWire, {s: 0.86, x: 960, y: 540, ry: 0}], [tComp, {s: 0.82, x: 960, y: 540}], [tComp + 30, {s: 0.78, x: 960, y: 560, r: 0.6}], [tCheck, {s: 0.8, x: 960, y: 540, r: 0}], [tBreak + 10, {s: 1.05, x: 760, y: 420}], [tFail, {s: 1.05, x: 1300, y: 640}], [tPick, {s: 0.82, x: 960, y: 540}]]}>
				<Abs x={browserX} y={560} center style={{transform: `translate(-50%,-50%) scale(${1 - phone * 0.12})`, filter: dimPick > 0 ? `blur(${dimPick * 6}px)` : undefined, opacity: 1 - dimPick * 0.4}}>
					<Browser><Site f={f} tParts={tParts} fill={fill} round={round} broken={broken} formState={formState} /></Browser>
				</Abs>
				<Abs x={960} y={560} center style={{opacity: life(f, W0 - 30, tParts[0] + 4, 8, 12), textAlign: 'center', whiteSpace: 'nowrap'}}>
					<div style={{fontFamily: FONT, fontSize: 30, letterSpacing: 4, fontWeight: 700, color: CRUST}}>THE JOB</div>
					<div style={{fontFamily: DISPLAY, fontSize: 88, fontWeight: 900, color: INK, marginTop: 8}}>A landing page for a small bakery</div>
				</Abs>
				{/* spec chips + file tree */}
				<Abs x={1560} y={560} center style={{opacity: side, transform: `translate(-50%,-50%) translateX(${(1 - side) * 120}px)`}}>
					{[['Clear spec', tClear], ['A few files', tFew], ['Easy to check', tEasy]].map(([t, at], i) => (
						<div key={i} style={{opacity: appear(f, at as number), transform: `translateX(${(1 - appear(f, at as number, 14)) * 40}px)`, marginBottom: 22, padding: '20px 28px', borderRadius: 18, background: '#fff', boxShadow: '0 16px 40px rgba(60,40,20,0.18)', fontFamily: FONT, fontWeight: 700, fontSize: 34, color: INK, display: 'flex', alignItems: 'center', gap: 16}}>
							<span style={{width: 34, height: 34, borderRadius: 34, background: C.sol, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 22}}>✓</span>{t as string}
						</div>
					))}
					<div style={{opacity: appear(f, tFew + 8), marginTop: 10, padding: '18px 26px', borderRadius: 16, background: '#2B1D12', fontFamily: MONO, fontSize: 24, color: '#F3D9B1', lineHeight: 1.6}}>
						index.html<br />styles.css<br />contact.js
					</div>
				</Abs>
				{/* complication: phone, speed, inbox */}
				<Abs x={1610} y={560} center style={{opacity: phone * (1 - kf(f, [tRounds - 4, tRounds + 8], [0, 1]) * 0), transform: `translate(-50%,-50%) translateX(${(1 - phone) * 300}px) rotate(${(1 - phone) * 8}deg)`}}>
					<Phone f={f} at={tPh + 4} />
				</Abs>
				<Abs x={1120} y={150} center style={{opacity: life(f, tLoad, tRounds + 6), transform: `translate(-50%,-50%) scale(${0.7 + 0.3 * pop(f, tLoad)})`}}>
					<div style={{padding: '14px 26px', borderRadius: 40, background: '#fff', boxShadow: '0 12px 30px rgba(60,40,20,0.2)', fontFamily: FONT, fontWeight: 800, fontSize: 30, color: '#2E9D6A'}}>⚡ Loads fast</div>
				</Abs>
				<Abs x={kf(f, [tSend, tSend + 30], [1260, 1700])} y={kf(f, [tSend, tSend + 15, tSend + 30], [700, 120, 210])} center style={{opacity: life(f, tSend, tRounds + 6)}}>
					<svg width={90} height={64} viewBox="0 0 90 64"><rect x={2} y={2} width={86} height={60} rx={8} fill="#fff" stroke={INK} strokeWidth={4} /><path d="M4,6 L45,38 L86,6" fill="none" stroke={INK} strokeWidth={4} /></svg>
				</Abs>
				<Abs x={1700} y={150} center style={{whiteSpace: 'nowrap', opacity: life(f, tSend + 10, tRounds + 6), fontFamily: FONT, fontWeight: 800, fontSize: 30, color: INK, background: '#fff', padding: '10px 20px', borderRadius: 14}}>Owner's inbox · 1 new</Abs>
				{/* revision rounds */}
				{['Bigger logo', 'Add a gluten-free item', 'Open Sundays'].map((t, i) => {
					const p = pop(f, roundsAt[i] - 16);
					return (
						<Abs key={t} x={250 + (i % 2) * 40} y={260 + i * 190} center style={{opacity: Math.min(1, p) * (1 - kf(f, [tMore + 30, tMore + 44], [0, 1])), transform: `translate(-50%,-50%) rotate(${-6 + i * 4}deg) scale(${0.6 + 0.4 * p})`}}>
							<div style={{width: 330, padding: '18px 22px', background: '#FFE58A', boxShadow: '0 14px 30px rgba(60,40,20,0.25)', fontFamily: FONT, color: INK}}>
								<div style={{fontSize: 20, fontWeight: 800, letterSpacing: 2}}>ROUND {i + 1}</div>
								<div style={{fontSize: 30, fontWeight: 700, marginTop: 4}}>{t}</div>
								<div style={{fontSize: 20, marginTop: 6, color: '#2E9D6A', fontWeight: 800, opacity: f > roundsAt[i] + 8 ? 1 : 0}}>✓ done</div>
							</div>
						</Abs>
					);
				})}
				{/* check callouts */}
				<Abs x={760} y={170} center style={{opacity: life(f, tBreak, tFail - 4), fontFamily: DISPLAY, fontWeight: 900, fontSize: 46, color: INK, background: '#fff', padding: '12px 26px', borderRadius: 16, boxShadow: '0 12px 30px rgba(60,40,20,0.2)', whiteSpace: 'nowrap'}}>
					Layout breaks? <span style={{color: C.red}}>You see it.</span>
				</Abs>
				<Abs x={1300} y={300} center style={{opacity: life(f, tFail, tPick - 2), fontFamily: DISPLAY, fontWeight: 900, fontSize: 46, color: INK, background: '#fff', padding: '12px 26px', borderRadius: 16, boxShadow: '0 12px 30px rgba(60,40,20,0.2)', whiteSpace: 'nowrap'}}>
					Form fails? <span style={{color: '#2E9D6A'}}>You know in seconds.</span>
				</Abs>
			</Camera>
			{/* recommendation */}
			<AbsoluteFill style={{background: `rgba(10,8,6,${dimPick * 0.45})`}} />
			<Pick f={f} at={tPick} m="sol" reason="Cheap to spot, cheap to fix. Iterate fast." y={kf(f, [tPass - 6, tPass + 14], [520, 330])} scale={kf(f, [tPass - 6, tPass + 14], [1, 0.8])} />
			<Abs x={960} y={690} center style={{opacity: appear(f, tPass + 10), textAlign: 'center'}}>
				<div style={{display: 'flex', gap: 60, alignItems: 'center', justifyContent: 'center'}}>
					<div style={{display: 'flex', gap: 12}}>
						{Array.from({length: 5}).map((_, i) => {
							const p = pop(f, word('passes', 'five') + i * 5);
							return <div key={i} style={{width: 100, height: 100, borderRadius: 22, background: C.sol, transform: `scale(${p})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: DISPLAY, fontWeight: 900, fontSize: 30, color: '#2B1500'}}>Sol</div>;
						})}
					</div>
					<div style={{fontFamily: DISPLAY, fontSize: 70, fontWeight: 900, color: '#fff', opacity: appear(f, word('passes', 'price'))}}>≈</div>
					<div style={{width: 100, height: 100, borderRadius: 22, background: C.astra, transform: `scale(${pop(f, word('passes', 'astra'))})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: DISPLAY, fontWeight: 900, fontSize: 26, color: '#04122B'}}>Astra</div>
				</div>
				<div style={{marginTop: 22}}><Tag color="#FFFFFF" style={{background: 'rgba(0,0,0,0.55)'}}>At FrontierCode 2.0's reported cost ratio · illustrative</Tag></div>
			</Abs>
		</AbsoluteFill>
	);
};
