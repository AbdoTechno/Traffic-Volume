/* ============================================================
   js/simulator.js
   Interactive Traffic Simulator — hour/day/weather/temp sliders
   ============================================================ */

const sHour     = document.getElementById('slider-hour');
const sDay      = document.getElementById('select-day');
const sWeather  = document.getElementById('select-weather');
const sTemp     = document.getElementById('slider-temp');
const sHoliday  = document.getElementById('check-holiday');

const bHour       = document.getElementById('sim-hour-badge');
const bTemp       = document.getElementById('sim-temp-badge');
const numVol      = document.getElementById('sim-vol-number');
const badgeStatus = document.getElementById('sim-status-badge');
const bTime       = document.getElementById('sim-break-time');
const bWeather    = document.getElementById('sim-break-weather');
const bCap        = document.getElementById('sim-break-cap');

// ── Traffic curves (vehicles/hr by hour index 0–23) ───────────
const WEEKDAY_CURVE = [
  550, 420, 380, 430, 900, 2500, 5200, 6100, 5800, 4600, 4300, 4600,
  4900, 4800, 5100, 5600, 6300, 6400, 5200, 3800, 3000, 2500, 1800, 1000,
];
const WEEKEND_CURVE = [
  1100, 750, 520, 400, 450, 680, 1150, 1750, 2600, 3400, 4000, 4400,
  4600, 4550, 4500, 4450, 4400, 4200, 3800, 3200, 2700, 2300, 1800, 1300,
];

const WEATHER_MODIFIERS = {
  clouds:     { mod: 0.98, text: '-2% (clouds)'     },
  rain_light: { mod: 0.92, text: '-8% (light rain)' },
  rain_heavy: { mod: 0.82, text: '-18% (heavy rain)'},
  snow_light: { mod: 0.85, text: '-15% (snow)'      },
  snow_heavy: { mod: 0.68, text: '-32% (heavy snow)'},
  fog:        { mod: 0.90, text: '-10% (fog)'       },
};

const CAPACITY = 7280; // max observed vehicles/hr on I-94

// ── Number animation ──────────────────────────────────────────
let _displayedVol = 0;
let _animFrame    = null;

function animateNumber(el, target) {
  const start     = _displayedVol;
  const startTime = performance.now();
  const duration  = 380;
  if (_animFrame) cancelAnimationFrame(_animFrame);

  function tick(now) {
    const t     = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(start + (target - start) * eased).toLocaleString();
    if (t < 1) {
      _animFrame = requestAnimationFrame(tick);
    } else {
      _displayedVol = target;
    }
  }
  _animFrame = requestAnimationFrame(tick);
}

// ── Hour formatter (AM/PM) ────────────────────────────────────
function formatH(h) {
  const p = h >= 12 ? 'PM' : 'AM';
  const d = h % 12 === 0 ? 12 : h % 12;
  return `${d < 10 ? '0' : ''}${d}:00 ${p}`;
}

// ── Diurnal label ─────────────────────────────────────────────
function diurnalLabel(h, day) {
  if (day !== 'weekday') return 'Weekend curve';
  if (h >= 7 && h <= 9)   return 'Morning peak commute';
  if (h >= 16 && h <= 18) return 'Evening peak commute';
  if (h <= 5)              return 'Night flow';
  return 'Midday traffic';
}

// ── Main update function ──────────────────────────────────────
function updateSim() {
  const h         = parseInt(sHour.value, 10);
  const day       = sDay.value;
  const weather   = sWeather.value;
  const temp      = parseInt(sTemp.value, 10);
  const isHoliday = sHoliday.checked;

  // Update badge displays
  bHour.textContent = formatH(h);
  bTemp.textContent = `${temp} °C (${temp + 273} K)`;

  // Calculate volume
  let base        = day === 'weekday' ? WEEKDAY_CURVE[h] : WEEKEND_CURVE[h];
  const wMod      = WEATHER_MODIFIERS[weather] || { mod: 1.0, text: '0% (clear)' };
  let modifier    = wMod.mod;

  if (temp < -15)  modifier *= 0.92;
  if (isHoliday)   base     *= 0.65;

  const vol = Math.round(base * modifier);

  // Animate the number
  animateNumber(numVol, vol);
  numVol.classList.remove('pulse');
  void numVol.offsetWidth; // restart animation
  numVol.classList.add('pulse');

  // Breakdown info
  bTime.textContent    = diurnalLabel(h, day);
  bWeather.textContent = wMod.text;
  bCap.textContent     = `${Math.min(100, Math.round((vol / CAPACITY) * 100))}% of highway capacity`;

  // Status badge
  let statusClass, statusText;
  if (vol > 5500) {
    statusText  = 'Severe congestion / peak rush';
    statusClass = 'st-rush';
  } else if (vol > 3600) {
    statusText  = 'Moderate commute flow';
    statusClass = 'st-mod';
  } else {
    statusText  = 'Light / free-flow traffic';
    statusClass = 'st-light';
  }
  badgeStatus.textContent = statusText;
  badgeStatus.className   = `status-badge ${statusClass}`;
  numVol.style.color =
    statusClass === 'st-rush' ? '#F2837A' :
    statusClass === 'st-mod'  ? '#F2A900' : '#1d2a36';
}

// ── Preset helper (called inline from HTML) ───────────────────
function setPreset(h, day, weather, temp, isHol) {
  sHour.value    = h;
  sDay.value     = day;
  sWeather.value = weather;
  sTemp.value    = temp;
  sHoliday.checked = isHol;
  updateSim();
}

// ── Event listeners ───────────────────────────────────────────
[sHour, sDay, sWeather, sTemp, sHoliday].forEach(el => {
  el.addEventListener('input',  updateSim);
  el.addEventListener('change', updateSim);
});

updateSim(); // initial render
