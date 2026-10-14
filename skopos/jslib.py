"""JavaScript helper library for SimHub formulas.

Each formula only gets the helpers it references (resolved transitively), so
formulas stay small. ES5 only, for SimHub's Jint engine.

Data sources, in order of preference:
  * iRacing raw telemetry / session data (always present, no plugin needed)
  * SimHub computed properties (fuel averages, relative on-track list)
  * Romainrob's iRacing Extra Properties (optional; used when installed)

Dashboard variables (fuel, shift, fieldOrder, ...) are computed once per frame
by SimHub; every consumer falls back to computing locally if the variable is
unavailable, so nothing breaks on older SimHub builds.
"""

import re

from .theme import FUEL_MARGIN_LAPS

FUNCS = {}


def fn(src):
    name = re.match(r"\s*function\s+(\w+)", src).group(1)
    FUNCS[name] = src.strip()


# ---- generic ------------------------------------------------------------------

fn("""function nz(v, d) { return (v === null || v === undefined || v === '' || (typeof v === 'number' && isNaN(v))) ? d : v; }""")
fn("""function P(k, d) { return nz($prop(k), d); }""")
fn("""function N(k, d) { var v = parseFloat($prop(k)); return isNaN(v) ? d : v; }""")
fn("""function B(k) { var v = $prop(k); return v === true || v === 'True' || v === 'true' || (typeof v === 'number' && v > 0) || v === '1'; }""")
fn("""function T(k, d) { return P('DataCorePlugin.GameRawData.Telemetry.' + k, d); }""")
fn("""function TN(k, d) { return N('DataCorePlugin.GameRawData.Telemetry.' + k, d); }""")
fn("""function S(k, d) { return P('DataCorePlugin.GameRawData.SessionData.' + k, d); }""")
fn("""function SN(k, d) { return N('DataCorePlugin.GameRawData.SessionData.' + k, d); }""")
fn("""function XP(k, d) { return P('IRacingExtraProperties.iRacing_' + k, d); }""")
fn("""function XN(k, d) { return N('IRacingExtraProperties.iRacing_' + k, d); }""")
fn("""function V(name, calc) { var v = $prop('variable.' + name); if (v === null || v === undefined || v === '') { v = calc(); } return v; }""")
fn("""function pad2(n) { return (n < 10 ? '0' : '') + n; }""")
fn("""function changeFade(key, v, ms) {
  // 1 the moment v changes, fading linearly to 0 over ms; 0 while v is steady
  if (typeof root === 'undefined' || v === null) { return 0; }
  var now = new Date().getTime(), st = root[key];
  if (!st) { root[key] = { v: v, t: 0 }; return 0; }
  if (Math.abs(v - st.v) > 0.0001) { st.t = now; }
  st.v = v;
  return st.t ? Math.max(0, 1 - (now - st.t) / ms) : 0;
}""")
fn("""function bbFade() { var f = +V('bbFade', function () { return changeFade('bb', N('BrakeBias', null), 2000); }); return isNaN(f) ? 0 : f; }""")
fn("""function hex2(n) { n = Math.max(0, Math.min(255, Math.round(n))); return (n < 16 ? '0' : '') + n.toString(16).toUpperCase(); }""")
fn("""function blinkOn(ms) { return Math.floor(new Date().getTime() / ms) % 2 === 0; }""")
fn("""function secs(t) {
  if (t === null || t === undefined) { return 0; }
  if (typeof t === 'number') { return t; }
  try { return timespantoseconds(t); } catch (e) { var v = parseFloat(t); return isNaN(v) ? 0 : v; }
}""")
fn("""function lapStr(s) {
  if (!(s > 0) || s > 5999) { return '-:--.---'; }
  var ms = Math.round(s * 1000), m = Math.floor(ms / 60000), r = ms - m * 60000;
  var sec = Math.floor(r / 1000), f = r - sec * 1000;
  return m + ':' + pad2(sec) + '.' + (f < 10 ? '00' : (f < 100 ? '0' : '')) + f;
}""")
fn("""function clockStr(s) {
  if (!(s >= 0) || s > 360000) { return '--:--'; }
  s = Math.floor(s);
  var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
  return (h > 0 ? h + ':' + pad2(m) : '' + m) + ':' + pad2(x);
}""")
fn("""function fx(v, dp) { return (v === null || v === undefined || isNaN(v)) ? '—' : (+v).toFixed(dp); }""")
fn("""function sgn(v, dp) {
  if (v === null || v === undefined || isNaN(v)) { return '—'; }
  var t = Math.abs(v).toFixed(dp);
  if (parseFloat(t) === 0) { return t; }
  return (v > 0 ? '+' : '−') + t;
}""")
fn("""function unitNum(s) { if (s === null || s === undefined) { return null; } var v = parseFloat(('' + s).replace(',', '.')); return isNaN(v) ? null : v; }""")
fn("""function shortName(n, max) {
  n = ('' + nz(n, '')).replace(/\\d+$/, '').replace(/^\\s+|\\s+$/g, '');
  if (n.length <= max) { return n; }
  var p = n.split(' ');
  if (p.length > 1) { n = p[0].charAt(0) + '. ' + p[p.length - 1]; }
  return n.length <= max ? n : n.substring(0, max - 1) + '…';
}""")
fn("""function arrAt(k, i) {
  try { var a = $prop('DataCorePlugin.GameRawData.Telemetry.' + k); if (a === null || a === undefined || i < 0) { return null; } var v = a[i]; return v === undefined ? null : v; }
  catch (e) { return null; }
}""")

# ---- session / track ------------------------------------------------------------

fn("""function trackLenM() {
  var s = '' + S('WeekendInfo.TrackLength', ''), v = unitNum(s);
  if (v === null) { return 0; }
  if (s.indexOf('mi') >= 0) { return v * 1609.344; }
  if (s.indexOf('km') < 0 && s.indexOf(' m') >= 0) { return v; }
  return v * 1000;
}""")
fn("""function timeLeft() { var t = TN('SessionTimeRemain', -1); return (t >= 0 && t < 500000) ? t : null; }""")
fn("""function refLap() {
  var best = TN('LapBestLapTime', 0), last = TN('LapLastLapTime', 0);
  if (best > 0) { return best * 1.01; }
  if (last > 0) { return last; }
  return SN('DriverInfo.DriverCarEstLapTime', 0);
}""")
fn("""function sessionLaps() {
  var s = P('DataCorePlugin.GameRawData.CurrentSessionInfo._SessionLaps', null);
  if (s !== null) { var n = parseInt(s, 10); return (n > 0 && n < 10000) ? n : 0; }
  var t = N('TotalLaps', 0); return (t > 0 && t < 10000) ? t : 0;
}""")
fn("""function lapsToGo() {
  // distance still to drive, in laps, counting the lap you are on
  if (B('Flag_Checkered')) { return 0; }
  var pct = TN('LapDistPct', 0); if (pct < 0 || pct > 1) { pct = 0; }
  if (B('Flag_White')) { return Math.max(0, 1 - pct); }            // white flag: this is the last lap
  var best = 1e9, total = sessionLaps(), done = TN('LapCompleted', N('CompletedLaps', 0));
  if (total > 0) { best = Math.max(0, total - done - pct); }
  var t = TN('SessionTimeRemain', -99999), lap = refLap();
  if (t > -10000 && t < 500000 && lap > 0) {
    // timed: the white flag comes at the first line crossing after the clock
    // runs out, then there is one more lap
    t = Math.max(0, t);
    var c1 = (1 - pct) * lap;
    var j = Math.max(1, Math.ceil((t - c1) / lap - 1e-9) + 1);
    best = Math.min(best, j + 1 - pct);
  }
  return best >= 1e9 ? null : best;
}""")
fn("""function lapsLeft() { var l = lapsToGo(); return l === null ? null : Math.ceil(l - 0.0001); }""")
fn("""function incidents() {
  var n = TN('PlayerCarMyIncidentCount', null); if (n === null) { n = TN('PlayerCarTeamIncidentCount', 0); }
  var lim = '' + S('WeekendInfo.WeekendOptions.IncidentLimit', '');
  var l = parseInt(lim, 10);
  return { n: n, limit: isNaN(l) ? null : l };
}""")

# ---- shift lights ---------------------------------------------------------------

fn("""function shiftCalc() {
  var r = N('Rpms', 0);
  var f = TN('PlayerCarSLFirstRPM', 0), s = TN('PlayerCarSLShiftRPM', 0);
  if (!(s > 0)) { f = SN('DriverInfo.DriverCarSLFirstRPM', 0); s = SN('DriverInfo.DriverCarSLShiftRPM', 0); }
  if (s > 0 && f > 0 && s > f) {
    if (r >= s) { return 99; }
    if (r < f) { return 0; }
    return Math.min(20, Math.floor((r - f) / (s - f) * 19) + 1);
  }
  if (B('CarSettings_RPMRedLineReached')) { return 99; }
  return Math.max(0, Math.min(20, Math.floor(N('CarSettings_CurrentDisplayedRPMPercent', 0) / 5)));
}""")
fn("""function shiftLeds() { return +V('shift', function () { return shiftCalc(); }); }""")

# ---- fuel -----------------------------------------------------------------------

fn("""function fuelCalc() {
  var fuel = TN('FuelLevel', N('Fuel', 0));
  var per = N('DataCorePlugin.Computed.Fuel_LitersPerLap', 0);
  var last = N('DataCorePlugin.Computed.Fuel_LastLapConsumption', 0);
  var cap = SN('DriverInfo.DriverCarFuelMaxLtr', 0) * SN('DriverInfo.DriverCarMaxFuelPct', 1);
  var laps = lapsToGo(), lap = refLap(), done = N('CompletedLaps', 0);
  var o = { fuel: fuel, per: per > 0 ? per : null, last: last > 0 ? last : null, cap: cap > 0 ? cap : null,
            tank: cap > 0 ? fuel / cap : null, laps: laps, tleft: timeLeft(), lof: null, tof: null,
            need: null, add: null, stops: null, save: null, savePct: null, wOpen: null, wClose: null };
  if (per > 0) { o.lof = fuel / per; o.tof = lap > 0 ? o.lof * lap : null; }
  if (laps !== null && per > 0) {
    o.need = laps * per;
    o.add = o.need - fuel + MARGIN * per;
    o.stops = o.add > 0 ? (cap > 0 ? Math.ceil(o.add / cap) : 1) : 0;
    o.save = laps > 0 ? fuel / laps : null;
    o.savePct = o.save !== null ? (o.save - per) / per : null;
    if (o.stops === 1 && cap > 0) {
      o.wOpen = done + 1 + Math.max(0, Math.ceil(laps - cap / per + MARGIN));
      o.wClose = done + Math.max(1, Math.floor(o.lof));
    }
  }
  return o;
}""".replace("MARGIN", repr(FUEL_MARGIN_LAPS)))
fn("""function fuelData() {
  try { return JSON.parse(V('fuel', function () { return JSON.stringify(fuelCalc()); })); } catch (e) { return {}; }
}""")

# ---- drivers (session info) -----------------------------------------------------

fn("""function drvBase(slot) { return 'DataCorePlugin.GameRawData.SessionData.DriverInfo.Drivers' + pad2(slot) + '.'; }""")
fn("""function drv(slot, f) { return slot > 0 ? $prop(drvBase(slot) + f) : null; }""")
fn("""function fieldOrderCalc() {
  var list = [];
  for (var i = 1; i <= 64; i++) {
    var b = drvBase(i), name = $prop(b + 'UserName');
    if (name === null || name === undefined || name === '') { continue; }
    if (B(b + 'CarIsPaceCar') || B(b + 'IsSpectator') || name === 'Pace Car') { continue; }
    list.push([i, '' + nz($prop(b + 'CarNumber'), '')]);
  }
  list.sort(function (a, c) {
    var x = parseInt(a[1], 10), y = parseInt(c[1], 10);
    if (isNaN(x)) { x = 99999; } if (isNaN(y)) { y = 99999; }
    if (x !== y) { return x - y; }
    return (a[1].length - c[1].length) || (a[0] - c[0]);
  });
  var out = [];
  for (var j = 0; j < list.length; j++) { out.push(list[j][0]); }
  return out.join(',');
}""")
fn("""function fieldSlots() { var s = '' + V('fieldOrder', function () { return fieldOrderCalc(); }); return s === '' ? [] : s.split(','); }""")
fn("""function fieldSlot(k) { var o = fieldSlots(), s = parseInt(o[k - 1], 10); return isNaN(s) ? 0 : s; }""")
fn("""function playerSlotCalc() {
  var idx = SN('DriverInfo.DriverCarIdx', -1);
  for (var i = 1; i <= 64; i++) { var c = $prop(drvBase(i) + 'CarIdx'); if (c !== null && c !== undefined && +c === idx) { return i; } }
  return 0;
}""")
fn("""function playerSlot() { return +V('playerSlot', function () { return playerSlotCalc(); }); }""")
fn("""function numSlotsCalc() {
  var m = {};
  for (var i = 1; i <= 64; i++) { var n = $prop(drvBase(i) + 'CarNumber'); if (n !== null && n !== undefined && n !== '') { m['' + n] = i; } }
  return JSON.stringify(m);
}""")
fn("""function slotByNum(n) {
  if (n === null || n === undefined || n === '') { return 0; }
  try { var m = JSON.parse(V('numSlots', function () { return numSlotsCalc(); })); return m['' + n] || 0; } catch (e) { return 0; }
}""")
fn("""function classesCalc() {
  var cpos = {};
  for (var p = 1; p <= 64; p++) {
    if (!lbOn(p)) { break; }
    var c = null; try { c = parseInt(driverclassposition(p), 10); } catch (e) { c = null; }
    if (c > 0) { cpos[lbNum(p)] = c; }
  }
  var cls = {}, order = [], slots = fieldSlots();
  for (var i = 0; i < slots.length; i++) {
    var s = +slots[i], id = '' + nz(drv(s, 'CarClassID'), ''), name = '' + nz(drv(s, 'CarClassShortName'), '');
    if (name === '') { name = '' + nz(drv(s, 'CarClassName'), 'Class'); }
    var key = id !== '' ? id : name;
    if (!cls[key]) { cls[key] = { name: name, color: clsColor(drv(s, 'CarClassColor')), est: +nz(drv(s, 'CarClassEstLapTime'), 0), rows: [] }; order.push(key); }
    var pos = arrAt('CarIdxClassPosition', +nz(drv(s, 'CarIdx'), -1));
    if (!(pos > 0)) { pos = cpos['' + nz(drv(s, 'CarNumber'), '')] || 0; }
    cls[key].rows.push([s, pos, +nz(drv(s, 'IRating'), 0)]);
  }
  var out = [], kk = 1600 / Math.LN2;
  for (var k = 0; k < order.length; k++) {
    var c2 = cls[order[k]], sum = 0, n = 0;
    c2.rows.sort(function (a, b) { var x = a[1] > 0 ? a[1] : 999, y = b[1] > 0 ? b[1] : 999; return (x - y) || (b[2] - a[2]); });
    for (var j = 0; j < c2.rows.length; j++) { if (c2.rows[j][2] > 0) { sum += Math.exp(-c2.rows[j][2] / kk); n++; } }
    out.push({ name: c2.name, color: c2.color, est: c2.est, n: c2.rows.length, sof: n > 0 ? Math.round(kk * Math.log(n / sum)) : 0,
               slots: c2.rows.map(function (r) { return r[0]; }), pos: c2.rows.map(function (r) { return r[1]; }) });
  }
  out.sort(function (a, b) { return (a.est > 0 ? a.est : 9999) - (b.est > 0 ? b.est : 9999); });
  return JSON.stringify(out);
}""")
fn("""function fieldTimingCalc() {
  // everyone in the session: cars with a lap time first (fastest first), then the rest by iRating
  var best = {}, last = {};
  for (var p = 1; p <= 64; p++) {
    if (!lbOn(p)) { break; }
    var n = lbNum(p), b = lbBest(p), l = lbLast(p);
    if (b > 0) { best[n] = b; }
    if (l > 0) { last[n] = l; }
  }
  var slots = fieldSlots(), rows = [];
  for (var i = 0; i < slots.length; i++) {
    var s = +slots[i], num = '' + nz(drv(s, 'CarNumber'), ''), ci = +nz(drv(s, 'CarIdx'), -1);
    var bt = best[num] || 0; if (!(bt > 0)) { var a = parseFloat(arrAt('CarIdxBestLapTime', ci)); if (a > 0) { bt = a; } }
    var lt = last[num] || 0; if (!(lt > 0)) { var a2 = parseFloat(arrAt('CarIdxLastLapTime', ci)); if (a2 > 0) { lt = a2; } }
    rows.push([s, bt, +nz(drv(s, 'IRating'), 0), lt]);
  }
  rows.sort(function (x, y) {
    var bx = x[1] > 0, by = y[1] > 0;
    if (bx && by) { return x[1] - y[1]; }
    if (bx !== by) { return bx ? -1 : 1; }
    return y[2] - x[2];
  });
  return JSON.stringify(rows);
}""")
fn("""function fieldTiming() { try { return JSON.parse(V('fieldTiming', function () { return fieldTimingCalc(); })) || []; } catch (e) { return []; } }""")
fn("""function classes() { try { return JSON.parse(V('classes', function () { return classesCalc(); })) || []; } catch (e) { return []; } }""")
fn("""function classCount() { return classes().length; }""")
fn("""function sofCalc() {
  var o = fieldSlots(), k = 1600 / Math.LN2, sum = 0, n = 0;
  for (var i = 0; i < o.length; i++) { var ir = parseFloat(drv(+o[i], 'IRating')); if (ir > 0) { sum += Math.exp(-ir / k); n++; } }
  return n > 0 ? Math.round(k * Math.log(n / sum)) : null;
}""")

# ---- licences / classes ---------------------------------------------------------

fn("""function licClass(l) {
  l = ('' + nz(l, '')).replace(/^\\s+/, '');
  if (!l) { return ''; }
  if (l.indexOf('Pro') === 0 || l.indexOf('WC') === 0 || l.indexOf('P ') === 0) { return 'P'; }
  return l.charAt(0).toUpperCase();
}""")
fn("""function licSR(l) { var m = ('' + nz(l, '')).match(/(\\d+\\.\\d+)/); return m ? m[1] : ''; }""")
fn("""function licText(l) { var c = licClass(l); return c ? (c + ' ' + licSR(l)) : '—'; }""")
fn("""function licBg(l) { var c = { R: '#FFD93A2B', D: '#FFF08A24', C: '#FFF2C230', B: '#FF3CB04E', A: '#FF2F6FE4', P: '#FF0B0E12' }[licClass(l)]; return c || '#FF1E252E'; }""")
fn("""function licFg(l) { var c = licClass(l); return (c === 'D' || c === 'C' || c === 'B') ? '#FF0B0E12' : '#FFF2F4F7'; }""")
fn("""function licTextCol(l) { var c = { R: '#FFFF5A4A', D: '#FFFF9A3C', C: '#FFF2C230', B: '#FF3CCB5A', A: '#FF4C8DFF', P: '#FFE6E8EB' }[licClass(l)]; return c || '#FFF2F4F7'; }""")
fn("""function clsColor(c) {
  if (typeof c === 'number') { c = c.toString(16); }
  var s = ('' + nz(c, '')).replace('0x', '').replace('#', '');
  if (s.length === 8) { return '#' + s.toUpperCase(); }
  while (s.length > 0 && s.length < 6) { s = '0' + s; }
  return s.length === 6 ? '#FF' + s.toUpperCase() : '#FFE6E8EB';
}""")
fn("""function irStr(v) { v = parseFloat(v); return v > 0 ? '' + Math.round(v) : '—'; }""")

# ---- your own session best --------------------------------------------------------
# The delta is iRacing's LapDeltaToSessionBestLap only (what iRacing's own delta
# bar shows for "session best"); when iRacing flags it invalid we show a dash
# instead of switching to another source.
#
# iRacing measures that delta against your best CLEAN lap of the session, but
# LapBestLapTime is your best lap including laps with incidents, so the two can
# disagree. refTrack() learns the real reference lap time: at every lap line
# the lap time minus the delta just before the line is exactly the reference
# used for that lap; a faster lap without an incident becomes the new one.

fn("""function myDeltaOK() { return B('DataCorePlugin.GameRawData.Telemetry.LapDeltaToSessionBestLap_OK'); }""")
fn("""function myDelta() { return myDeltaOK() ? TN('LapDeltaToSessionBestLap', 0) : 0; }""")
fn("""function refTrack() {
  if (typeof root === 'undefined') { return -1; }
  var now = new Date().getTime();
  var sess = TN('SessionNum', 0), lapc = TN('LapCompleted', N('CompletedLaps', 0)), pct = TN('LapDistPct', 0);
  var d = TN('LapDeltaToSessionBestLap', 0), last = TN('LapLastLapTime', 0), inc = TN('PlayerCarMyIncidentCount', 0);
  var st = root.rt;
  if (!st || st.sess !== sess) { st = root.rt = { sess: sess, lap: lapc, inc0: inc, dEnd: null, pend: null, seen: last, ref: -1 }; }
  if (lapc === st.lap) {
    if (myDeltaOK() && pct > 0.8) { st.dEnd = d; }
  } else {
    if (lapc > st.lap) { st.pend = { dEnd: st.dEnd, clean: inc === st.inc0, t0: now }; }
    st.lap = lapc; st.inc0 = inc; st.dEnd = null;
  }
  if (st.pend && last > 0 && last !== st.seen) {
    var p = st.pend, used = p.dEnd === null ? -1 : last - p.dEnd;
    if (used > 0) { st.ref = (p.clean && last < used - 0.0005) ? last : used; }
    else if (p.clean && (st.ref <= 0 || last < st.ref)) { st.ref = last; }
    st.seen = last; st.pend = null;
  } else if (st.pend && now - st.pend.t0 > 5000) { st.pend = null; st.seen = last; }
  return st.ref;
}""")
fn("""function myRef() { var r = +V('myRef', function () { return refTrack(); }); return r > 0 ? r : 0; }""")
fn("""function myBest() {
  var r = myRef(); if (r > 0) { return r; }
  var b = TN('LapBestLapTime', 0); return b > 0 ? b : secs($prop('DataCorePlugin.GameData.BestLapTime'));
}""")
fn("""function predicted() {
  var r = myRef();
  if (r > 0 && myDeltaOK()) { return r + TN('LapDeltaToSessionBestLap', 0); }
  var last = TN('LapLastLapTime', 0);
  if (last > 0 && B('DataCorePlugin.GameRawData.Telemetry.LapDeltaToSessionLastlLap_OK')) { return last + TN('LapDeltaToSessionLastlLap', 0); }
  return 0;
}""")

# ---- leaderboard (race position order, SimHub built-in functions) ---------------
# Position p is 1-based. Every call is guarded so a missing function or an empty
# position degrades to a blank instead of an error.

fn("""function lbName(p) { try { return p >= 1 ? '' + nz(drivername(p), '') : ''; } catch (e) { return ''; } }""")
fn("""function lbOn(p) { return lbName(p) !== ''; }""")
fn("""function lbNum(p) { try { return '' + nz(drivercarnumber(p), ''); } catch (e) { return ''; } }""")
fn("""function lbLic(p) {
  var l = null; try { l = driverlicencestring(p); } catch (e) { l = null; }
  if (l === null || l === undefined || l === '') { l = drv(slotByNum(lbNum(p)), 'LicString'); }
  return nz(l, '');
}""")
fn("""function lbIR(p) {
  var v = null; try { v = driveriracingirating(p); } catch (e) { v = null; }
  if (!(parseFloat(v) > 0)) { v = drv(slotByNum(lbNum(p)), 'IRating'); }
  return v;
}""")
fn("""function lbCls(p) {
  var c = null; try { c = drivercarclasscolor(p); } catch (e) { c = null; }
  if (c === null || c === undefined || c === '') { c = drv(slotByNum(lbNum(p)), 'CarClassColor'); }
  return clsColor(c);
}""")
fn("""function lbLast(p) { try { return secs(driverlastlap(p)); } catch (e) { return 0; } }""")
fn("""function lbBest(p) { try { return secs(driverbestlap(p)); } catch (e) { return 0; } }""")
fn("""function lbLap(p) { try { var v = parseFloat(drivercurrentlap(p)); return isNaN(v) ? null : v; } catch (e) { return null; } }""")
fn("""function lbGapLeader(p) { try { var g = parseFloat(secs(drivergaptoleader(p))); return isNaN(g) ? null : Math.abs(g); } catch (e) { return null; } }""")
fn("""function lbGapTo(p) {
  var g = null; try { g = parseFloat(secs(drivergaptoplayer(p))); } catch (e) { g = null; }
  if (g === null || isNaN(g)) { var a = lbGapLeader(p), b = lbGapLeader(myPos()); g = (a === null || b === null) ? null : a - b; }
  return g === null ? null : Math.abs(g);
}""")
fn("""function lbCar(p) {
  var s = slotByNum(lbNum(p)), c = drv(s, 'CarScreenNameShort');
  if (c === null || c === undefined || c === '') { c = drv(s, 'CarScreenName'); }
  if (c === null || c === undefined || c === '') { try { c = drivercarname(p); } catch (e) { c = null; } }
  return '' + nz(c, '');
}""")
fn("""function myPos() { var p = N('PlayerLeaderboardPosition', 0); return p > 0 ? p : N('Position', 0); }""")
fn("""function lbCountCalc() { var n = 0; for (var p = 1; p <= 64; p++) { if (!lbOn(p)) { break; } n = p; } return n; }""")
fn("""function lbCount() { return Math.max(+V('lbCount', function () { return lbCountCalc(); }), myPos()); }""")
fn("""function standPos(i) {
  var me = myPos();
  if (i <= 3 || me <= 7) { return i; }
  return Math.max(4, Math.min(me - 4, lbCount() - 7)) + i - 4;
}""")
fn("""function sessBestCalc() {
  var t = 0, who = '', pos = 0;
  for (var p = 1; p <= 64; p++) {
    if (!lbOn(p)) { break; }
    var b = lbBest(p);
    if (b > 0 && (t === 0 || b < t)) { t = b; who = lbName(p); pos = p; }
  }
  var mine = TN('LapBestLapTime', 0);
  if (mine > 0 && (t === 0 || mine <= t + 0.0005)) { t = mine; pos = myPos(); who = ''; }
  return { t: t, name: who, mine: pos > 0 && pos === myPos(), pos: pos };
}""")
fn("""function sessBest() { try { return JSON.parse(V('sessBest', function () { return JSON.stringify(sessBestCalc()); })); } catch (e) { return { t: 0, name: '', mine: false, pos: 0 }; } }""")

# ---- relative (on-track, SimHub PersistantTracker) ------------------------------
# Row index 1..11: 1-5 cars ahead (farthest first), 6 = player, 7-11 behind.

REL_AHEAD = 5
REL_PLAYER = REL_AHEAD + 1

fn("""function relKey(i) { if (i <= 5) { return 'Ahead_' + pad2(5 - i); } if (i === 6) { return null; } return 'Behind_' + pad2(i - 7); }""")
fn("""function relP(i, f) { var k = relKey(i); return k === null ? null : $prop('PersistantTrackerPlugin.Driver' + k + '_' + f); }""")
fn("""function relX(i, f) { var k = relKey(i); return k === null ? null : $prop('IRacingExtraProperties.iRacing_Driver' + k + '_' + f); }""")
fn("""function relOn(i) { if (i === 6) { return true; } var n = relP(i, 'Name'); return !(n === null || n === undefined || n === ''); }""")
fn("""function relSlot(i) { return i === 6 ? playerSlot() : slotByNum(relP(i, 'CarNumber')); }""")
fn("""function relLic(i) {
  var l = i === 6 ? XP('Player_LicenceString', null) : relX(i, 'LicenceString');
  if (l === null || l === undefined || l === '') { l = drv(relSlot(i), 'LicString'); }
  return nz(l, '');
}""")
fn("""function relIR(i) {
  var v = i === 6 ? null : relP(i, 'IRating');
  if (!(parseFloat(v) > 0)) { v = drv(relSlot(i), 'IRating'); }
  return v;
}""")

# car directly ahead / behind on track: k = 'Ahead_00' or 'Behind_00'
fn("""function nearP(k, f) { return $prop('PersistantTrackerPlugin.Driver' + k + '_' + f); }""")
fn("""function nearOn(k) { var n = nearP(k, 'Name'); return !(n === null || n === undefined || n === ''); }""")
fn("""function nearSlot(k) { return slotByNum(nearP(k, 'CarNumber')); }""")
fn("""function nearLic(k) {
  var l = $prop('IRacingExtraProperties.iRacing_Driver' + k + '_LicenceString');
  if (l === null || l === undefined || l === '') { l = drv(nearSlot(k), 'LicString'); }
  return nz(l, '');
}""")
fn("""function nearIR(k) { var v = nearP(k, 'IRating'); if (!(parseFloat(v) > 0)) { v = drv(nearSlot(k), 'IRating'); } return v; }""")
fn("""function nearCar(k) {
  var s = nearSlot(k), c = drv(s, 'CarScreenNameShort');
  if (c === null || c === undefined || c === '') { c = drv(s, 'CarScreenName'); }
  if (c === null || c === undefined || c === '') { c = nearP(k, 'CarName'); }
  return '' + nz(c, '');
}""")
fn("""function nearGap(k) { var g = parseFloat(nearP(k, 'Gap')); return isNaN(g) ? null : Math.abs(g); }""")

# ---- pit ------------------------------------------------------------------------

fn("""function pitLimitKph() {
  var x = XN('PitSpeedLimitKph', 0);
  if (x > 0) { return x; }
  var s = '' + S('WeekendInfo.TrackPitSpeedLimit', ''), v = unitNum(s);
  if (v === null) { return 0; }
  return s.indexOf('mph') >= 0 ? v * 1.609344 : v;
}""")
fn("""function pitBoxDist() {
  var box = SN('DriverInfo.DriverPitTrkPct', -1), pct = TN('LapDistPct', -1), L = trackLenM();
  if (box > 0 && pct >= 0 && L > 0) {
    var d = box - pct;
    if (d < -0.5) { d += 1; } if (d > 0.5) { d -= 1; }
    return d * L;
  }
  var x = XN('DistanceToPitBox', NaN);
  return isNaN(x) ? null : x;
}""")
fn("""function inStall() { return B('DataCorePlugin.GameRawData.Telemetry.PlayerCarInPitStall'); }""")
fn("""function onPitRoad() { return B('IsInPitLane') || B('DataCorePlugin.GameRawData.Telemetry.OnPitRoad'); }""")
fn("""function limiterOn() { return B('PitLimiterOn'); }""")
fn("""function garageMode() {
  return B('DataCorePlugin.GameRunning') && (B('DataCorePlugin.GameRawData.Telemetry.IsInGarage') || !B('DataCorePlugin.GameRawData.Telemetry.IsOnTrack'));
}""")

# ---- weather --------------------------------------------------------------------

fn("""function airT() { var v = N('AirTemperature', null); return v === null ? TN('AirTemp', null) : v; }""")
fn("""function trackT() { var v = N('RoadTemperature', null); return v === null ? TN('TrackTempCrew', null) : v; }""")
fn("""function trend(key, v, win) {
  if (v === null || typeof root === 'undefined') { return null; }
  var now = new Date().getTime() / 1000;
  if (!root[key]) { root[key] = []; }
  var a = root[key];
  if (a.length === 0 || now - a[a.length - 1][0] >= 20) { a.push([now, v]); }
  while (a.length > 2 && now - a[1][0] > win) { a.shift(); }
  if (a.length < 2 || now - a[0][0] < 60) { return null; }
  return v - a[0][1];
}""")
fn("""function compass(rad) { var d = ((rad * 180 / Math.PI) % 360 + 360) % 360; return ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.round(d / 45) % 8]; }""")
fn("""function skiesStr(v) { return ['Clear', 'Partly cloudy', 'Mostly cloudy', 'Overcast'][+v] || '—'; }""")
fn("""function wetStr(v) { return ['—', 'Dry', 'Mostly dry', 'Very lightly wet', 'Lightly wet', 'Moderately wet', 'Very wet', 'Extremely wet'][+v] || '—'; }""")
fn("""function hPa(v) { if (v === null) { return null; } if (v > 2000) { return v / 100; } if (v > 500) { return v; } return v * 33.8639; }""")
fn("""function rubber() {
  var r = P('DataCorePlugin.GameRawData.CurrentSessionInfo._SessionTrackRubberState', null);
  if (r === null) { r = P('DataCorePlugin.GameRawData.CurrentSessionInfo.SessionTrackRubberState', null); }
  return r === null ? '—' : ('' + r);
}""")


_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def program(body):
    """Return a complete formula: needed helpers followed by `body`."""
    needed, queue = [], [body]
    while queue:
        src = queue.pop()
        for name in _CALL.findall(src):
            if name in FUNCS and name not in needed:
                needed.append(name)
                queue.append(FUNCS[name])
    order = [n for n in FUNCS if n in needed]  # stable, definition order
    return "\n".join([FUNCS[n] for n in order] + [body.strip()])
