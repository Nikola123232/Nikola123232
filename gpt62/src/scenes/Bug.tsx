import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Badge, C, Camera, Count, DISPLAY, FONT, MONO, Pick, appear, cue, kf, life, pop, word, easeInOut} from '../lib';

const BG = '#07090C', GRN = '#7CF5B4';
type Node = {id: string; x: number; y: number; code: string[]; hot?: number};
const NODES: Node[] = [
	{id: 'receipt.py', x: 1500, y: 520, code: ['def render(order):', '  line("Subtotal", order.subtotal)', '  line("Discount", order.discount)', '  line("Total", order.total)  # 35.69 ?!'], hot: 3},
	{id: 'cart.py', x: 940, y: 250, code: ['subtotal = to_money(sum(prices))', 'total = apply_discount(', '    subtotal, coupon)', 'return Order(subtotal, total)']},
	{id: 'currency.py', x: 380, y: 520, code: ['def to_money(x, cur):', '  step = STEP[cur]', '  return floor(x / step) * step', '  # EUR: step = 0.01']},
	{id: 'discount_rules.py', x: 940, y: 800, code: ['def apply_discount(amt, code):', '  pct = RULES[code]  # SAVE15', '  return to_money(amt * (1-pct))', '  # changed 4 months ago']},
];
const EDGES: [string, string][] = [['receipt.py', 'cart.py'], ['cart.py', 'currency.py'], ['cart.py', 'discount_rules.py'], ['discount_rules.py', 'currency.py']];
const N = (id: string) => NODES.find((n) => n.id === id)!;

const FileCard: React.FC<{n: Node; f: number; lit: number; fine: number; hotOn: boolean; warn?: string; warnOn?: number}> = ({n, f, lit, fine, hotOn, warn, warnOn = 0}) => (
	<Abs x={n.x} y={n.y} center style={{opacity: 0.35 + 0.65 * lit, transform: `translate(-50%,-50%) scale(${0.94 + 0.06 * lit})`}}>
		<div style={{width: 500, borderRadius: 16, background: '#0E1217', border: `2px solid ${lit > 0.5 ? (hotOn ? C.red : '#2D3A48') : '#1A222C'}`, boxShadow: lit > 0.5 ? `0 0 50px ${hotOn ? C.red + '44' : 'rgba(0,0,0,0.5)'}` : undefined, overflow: 'hidden', position: 'relative'}}>
			<div style={{padding: '12px 18px', background: '#141A21', fontFamily: MONO, fontSize: 22, color: '#C9D4E0', display: 'flex', justifyContent: 'space-between'}}>
				<span>{n.id}</span>
				<span style={{color: C.green, opacity: fine, fontWeight: 700}}>✓ looks fine</span>
			</div>
			<div style={{padding: '14px 18px', fontFamily: MONO, fontSize: 21, lineHeight: 1.6}}>
				{n.code.map((l, i) => (
					<div key={i} style={{whiteSpace: 'pre', color: l.trim().startsWith('#') || l.includes('  #') && i === n.code.length - 1 ? '#6B7A8C' : '#D7E1EC', background: hotOn && n.hot === i ? 'rgba(255,90,96,0.18)' : 'transparent', borderRadius: 4}}>{l}</div>
				))}
			</div>
			{warn && <div style={{position: 'absolute', right: 14, bottom: 12, opacity: warnOn, padding: '6px 12px', borderRadius: 8, background: C.sol, color: '#1B0F02', fontFamily: FONT, fontWeight: 800, fontSize: 18}}>{warn}</div>}
		</div>
	</Abs>
);

export const Bug: React.FC<{f: number}> = ({f}) => {
	const B0 = cue('bug'), tCent = cue('cent'), tSome = word('cent', 'sometimes'), tTrace = cue('trace'), tNot = word('trace', 'isn');
	const tChain = cue('chain'), tCart = word('chain', 'cart'), tCur = word('chain', 'currency'), tDisc = word('chain', 'discount'), tMonths = word('chain', 'months');
	const tCoupon = cue('coupon'), tComp = cue('bugcomp'), tFine = word('bugcomp', 'fine'), tConn = cue('connect'), tWrong = cue('wrongfix'), tShips = word('wrongfix', 'ships'), tQuiet = word('wrongfix', 'quietly');
	const tPick = cue('bugpick'), tHand = cue('handoff'), tHandA = word('handoff', 'then');
	
	const lit = (id: string) => {
		const at = {'receipt.py': tTrace, 'cart.py': tCart, 'currency.py': tCur, 'discount_rules.py': tDisc}[id]!;
		return kf(f, [at - 4, at + 10], [0, 1]);
	};
	const graphOp = life(f, tTrace - 6, tWrong + 4, 10, 10) * (1 - kf(f, [tCoupon - 4, tCoupon + 8], [0, 1]) + kf(f, [tComp - 6, tComp + 6], [0, 1]));
	const fine = kf(f, [tFine - 6, tFine + 8], [0, 1]);
	const connRed = kf(f, [tConn, tConn + 10], [0, 1]);
	// trace path progress per edge
	const edgeP = (a: string, b: string) => {
		const at = a === 'receipt.py' ? tCart - 14 : b === 'currency.py' && a === 'cart.py' ? tCur - 12 : a === 'cart.py' ? tDisc - 12 : tMonths;
		return kf(f, [at, at + 14], [0, 1]);
	};
	return (
		<AbsoluteFill style={{background: BG}}>
			{/* faint code-rain texture */}
			<AbsoluteFill style={{opacity: 0.07, fontFamily: MONO, fontSize: 18, color: GRN, lineHeight: 1.4, whiteSpace: 'pre', overflow: 'hidden', transform: `translateY(${-(f % 400) * 0.5}px)`}}>
				{Array.from({length: 60}).map((_, i) => <div key={i}>{'  '.repeat(i % 7)}{['assert total == expected', 'Decimal("0.01")', 'round(x, 2)', 'RULES["SAVE15"] = 0.15', 'def checkout(cart):', 'log.debug(order)', 'git blame discount_rules.py'][i % 7]}</div>)}
			</AbsoluteFill>
			{/* 1. the symptom */}
			<AbsoluteFill style={{opacity: life(f, B0 - 4, tTrace + 4, 8, 10)}}>
				<Camera f={f} keys={[[B0, {s: 1.1}], [tTrace, {s: 1.0}]]}>
					<Abs x={700} y={500} center>
						<div style={{width: 560, padding: '36px 40px', background: '#F4F1EA', color: '#1A1A1A', fontFamily: MONO, fontSize: 30, lineHeight: 1.7, borderRadius: 6, boxShadow: '0 40px 100px rgba(0,0,0,0.6)', transform: 'rotate(-2deg)'}}>
							<div style={{textAlign: 'center', fontWeight: 800, letterSpacing: 4}}>RECEIPT</div>
							<div style={{borderTop: '2px dashed #999', margin: '12px 0'}} />
							<div style={{display: 'flex', justifyContent: 'space-between'}}><span>Subtotal</span><span>42.00</span></div>
							<div style={{display: 'flex', justifyContent: 'space-between'}}><span>SAVE15</span><span>-6.30</span></div>
							<div style={{display: 'flex', justifyContent: 'space-between', fontWeight: 800, color: appear(f, tCent + 10) > 0.5 ? '#D3262E' : '#1A1A1A'}}><span>Total</span><span>35.69</span></div>
							<div style={{fontSize: 22, color: '#D3262E', opacity: appear(f, tCent + 16)}}>expected 35.70</div>
						</div>
					</Abs>
					<Abs x={1360} y={500} center style={{opacity: appear(f, tSome - 6)}}>
						<div style={{fontFamily: FONT, fontSize: 30, color: C.dim, marginBottom: 18, letterSpacing: 2, fontWeight: 700}}>100 TEST CHECKOUTS</div>
						<div style={{display: 'grid', gridTemplateColumns: 'repeat(10, 44px)', gap: 10}}>
							{Array.from({length: 100}).map((_, i) => {
								const bad = [7, 38, 61, 84].includes(i);
								const on = f > tSome - 6 + i * 0.4;
								return <div key={i} style={{width: 44, height: 44, borderRadius: 8, background: !on ? '#151B22' : bad ? C.red : '#1F4A37', boxShadow: bad && on ? `0 0 16px ${C.red}` : undefined}} />;
							})}
						</div>
						<div style={{fontFamily: FONT, fontSize: 28, color: C.red, marginTop: 16, fontWeight: 700, opacity: appear(f, tSome + 30)}}>Only sometimes.</div>
					</Abs>
				</Camera>
			</AbsoluteFill>
			{/* 2. the trace through connected files (one world, camera follows the red line) */}
			<AbsoluteFill style={{opacity: graphOp}}>
				<Camera f={f} keys={[[tTrace, {s: 1.35, x: 1500, y: 520}], [tCart - 10, {s: 1.35, x: 1500, y: 520}], [tCart + 10, {s: 1.2, x: 1080, y: 380}], [tCur + 8, {s: 1.15, x: 520, y: 500}], [tDisc + 8, {s: 1.1, x: 900, y: 690}], [tMonths + 30, {s: 1.05, x: 900, y: 660}], [tComp - 4, {s: 0.86, x: 940, y: 520}], [tConn + 10, {s: 0.9, x: 700, y: 640}], [tWrong, {s: 0.88, x: 900, y: 540}]]}>
					<svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
						{EDGES.map(([a, b]) => {
							const A = N(a), Bn = N(b), p = edgeP(a, b);
							const isConn = a === 'discount_rules.py' || (a === 'cart.py' && b === 'currency.py');
							const col = isConn && connRed > 0 ? C.red : C.red;
							return (
								<g key={a + b}>
									<line x1={A.x} y1={A.y} x2={Bn.x} y2={Bn.y} stroke="#223040" strokeWidth={4} strokeDasharray="8 10" />
									<line x1={A.x} y1={A.y} x2={A.x + (Bn.x - A.x) * p} y2={A.y + (Bn.y - A.y) * p} stroke={col} strokeWidth={isConn ? 4 + connRed * 6 * (0.6 + 0.4 * Math.sin(f / 4)) : 4} strokeOpacity={0.9} />
								</g>
							);
						})}
					</svg>
					{NODES.map((n) => (
						<FileCard key={n.id} n={n} f={f} lit={Math.max(lit(n.id), kf(f, [tComp - 6, tComp + 6], [0, 1]))} fine={fine} hotOn={n.id === 'receipt.py' ? f > tTrace + 10 : false}
							warn={n.id === 'discount_rules.py' ? 'changed 4 months ago' : undefined} warnOn={appear(f, tMonths)} />
					))}
					<Abs x={1500} y={330} center style={{opacity: life(f, tNot, tCart + 6), fontFamily: DISPLAY, fontSize: 40, fontWeight: 800, color: C.red, whiteSpace: 'nowrap'}}>✕ Symptom here. Cause isn't.</Abs>
					<Abs x={400} y={770} center style={{opacity: kf(f, [tConn + 6, tConn + 18], [0, 1]), transform: 'translate(-50%,-50%) rotate(-3deg)'}}>
						<div style={{padding: '16px 24px', borderRadius: 14, background: '#2A0B0E', border: `2px solid ${C.red}`, fontFamily: FONT, fontWeight: 700, fontSize: 30, color: '#FFD1D3', whiteSpace: 'nowrap'}}>
							floor() after the discount → 35.69, not 35.70
						</div>
					</Abs>
					<Abs x={940} y={1010} center style={{opacity: life(f, tFine, tConn + 4), fontFamily: DISPLAY, fontSize: 44, fontWeight: 800, color: C.green, whiteSpace: 'nowrap'}}>Every file looks fine on its own</Abs>
				</Camera>
			</AbsoluteFill>
			{/* 3. reproduction matrix */}
			<AbsoluteFill style={{opacity: life(f, tCoupon - 4, tComp, 10, 10)}}>
				<Abs x={960} y={200} center style={{fontFamily: DISPLAY, fontSize: 56, fontWeight: 800, whiteSpace: 'nowrap'}}>Reproduces only in one combination</Abs>
				<Abs x={960} y={560} center>
					<div style={{display: 'grid', gridTemplateColumns: '220px repeat(4, 200px)', gap: 12, fontFamily: MONO, fontSize: 28}}>
						<div />
						{['USD', 'EUR', 'GBP', 'JPY'].map((c) => <div key={c} style={{textAlign: 'center', color: C.dim, padding: 10}}>{c}</div>)}
						{['none', 'SAVE10', 'SAVE15'].map((cp, r) => (
							<React.Fragment key={cp}>
								<div style={{color: C.dim, padding: '28px 10px', textAlign: 'right'}}>{cp}</div>
								{[0, 1, 2, 3].map((c) => {
									const bad = r === 2 && c === 1, on = f > tCoupon + 6 + (r * 4 + c) * 3;
									const reveal = bad && f > word('coupon', 'currency');
									return <div key={c} style={{height: 90, borderRadius: 14, background: !on ? '#11161C' : reveal ? C.red : '#173A2B', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 34, transform: `scale(${reveal ? 1.08 : 1})`, boxShadow: reveal ? `0 0 40px ${C.red}` : undefined}}>{on ? (reveal ? '✕ 1¢' : '✓') : ''}</div>;
								})}
							</React.Fragment>
						))}
					</div>
				</Abs>
			</AbsoluteFill>
			{/* 4. the wrong fix ships */}
			<AbsoluteFill style={{opacity: life(f, tWrong - 2, tPick + 30, 10, 14)}}>
				<Abs x={620} y={480} center style={{transform: `translate(-50%,-50%) translateY(${(1 - appear(f, tWrong, 16)) * 60}px)`}}>
					<div style={{width: 640, borderRadius: 16, background: '#0E1217', border: '2px solid #2D3A48', overflow: 'hidden'}}>
						<div style={{padding: '12px 18px', background: '#141A21', fontFamily: MONO, fontSize: 22, color: '#C9D4E0'}}>hotfix: patch receipt total</div>
						<div style={{padding: '16px 18px', fontFamily: MONO, fontSize: 24, lineHeight: 1.6}}>
							<div style={{color: '#9FF0CB', background: 'rgba(56,217,154,0.12)', padding: '0 8px'}}>+ if total % 0.05: total += 0.01</div>
						</div>
						<div style={{padding: '12px 18px 18px', fontFamily: FONT, fontWeight: 700, fontSize: 26, color: C.green, opacity: appear(f, tShips)}}>✓ Tests pass · Deployed</div>
					</div>
				</Abs>
				<Abs x={1360} y={480} center style={{opacity: appear(f, tQuiet - 4), textAlign: 'center'}}>
					<div style={{fontFamily: FONT, fontSize: 28, letterSpacing: 3, color: C.dim, fontWeight: 700}}>ORDERS CHARGED WRONG</div>
					<div style={{fontFamily: DISPLAY, fontSize: 150, fontWeight: 900, color: C.red}}><Count f={f} a={tQuiet} b={tPick + 30} to={1284} dec={0} /></div>
					<div style={{fontFamily: FONT, fontSize: 26, color: C.dim}}>no errors · no alerts</div>
				</Abs>
			</AbsoluteFill>
			{/* 5. pick + handoff */}
			<AbsoluteFill style={{background: `rgba(0,0,0,${kf(f, [tPick - 4, tPick + 10], [0, 0.55])})`}} />
			<Pick f={f} at={tPick} m="astra" reason="Hard to verify. Expensive when it's wrong." y={kf(f, [tHand - 12, tHand + 8], [520, 300])} scale={kf(f, [tHand - 12, tHand + 8], [1, 0.8])} />
			<Abs x={960} y={kf(f, [tHand - 6, tHand + 14], [1100, 640])} center style={{opacity: appear(f, tHand - 6)}}>
				<div style={{display: 'flex', alignItems: 'center', gap: 30}}>
					<div style={{padding: '22px 30px', borderRadius: 18, border: `2px solid ${C.sol}`, background: '#1E1306', minWidth: 400}}>
						<Badge m="sol" size={36} />
						<div style={{fontFamily: FONT, fontSize: 28, color: C.ink, marginTop: 8}}>Reproduce the bug<br />Add logging</div>
					</div>
					<div style={{fontFamily: DISPLAY, fontSize: 60, color: C.ink, opacity: appear(f, tHandA)}}>→</div>
					<div style={{padding: '22px 30px', borderRadius: 18, border: `2px solid ${C.astra}`, background: '#081734', minWidth: 400, opacity: appear(f, tHandA), transform: `scale(${0.8 + 0.2 * pop(f, tHandA)})`}}>
						<Badge m="astra" size={36} />
						<div style={{fontFamily: FONT, fontSize: 28, color: C.ink, marginTop: 8}}>Trace the cause<br />Write the fix</div>
					</div>
				</div>
			</Abs>
		</AbsoluteFill>
	);
};
void easeInOut;
