const sHour = document.getElementById('slider-hour');
const sDay = document.getElementById('select-day');
const sWeather = document.getElementById('select-weather');
const sTemp = document.getElementById('slider-temp');
const sHoliday = document.getElementById('check-holiday');

const bHour = document.getElementById('sim-hour-badge');
const bTemp = document.getElementById('sim-temp-badge');
const numVol = document.getElementById('sim-vol-number');
const badgeStatus = document.getElementById('sim-status-badge');
const bTime = document.getElementById('sim-break-time');
const bWeather = document.getElementById('sim-break-weather');
const bCap = document.getElementById('sim-break-cap');

const weekdayCurve = [
  550, 420, 380, 430, 900, 2500, 5200, 6100, 5800, 4600, 4300, 4600,
  4900, 4800, 5100, 5600, 6300, 6400, 5200, 3800, 3000, 2500, 1800, 1000
];
const weekendCurve = [
  1100, 750, 520, 400, 450, 680, 1150, 1750, 2600, 3400, 4000, 4400,
  4600, 4550, 4500, 4450, 4400, 4200, 3800, 3200, 2700, 2300, 1800, 1300
];

let displayedVol = 0;
let numberAnimFrame = null;
function animateNumber(el, target) {
  const start = displayedVol;
  const startTime = performance.now();
  const duration = 380;
  if (numberAnimFrame) cancelAnimationFrame(numberAnimFrame);
  function tick(now) {
    const t = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = Math.round(start + (target - start) * eased);
    el.textContent = val.toLocaleString();
    if (t < 1) {
      numberAnimFrame = requestAnimationFrame(tick);
    } else {
      displayedVol = target;
    }
  }
  numberAnimFrame = requestAnimationFrame(tick);
}

function formatH(h) {
  const p = h >= 12 ? 'PM' : 'AM';
  const d = h % 12 === 0 ? 12 : h % 12;
  return `${d < 10 ? '0' : ''}${d}:00 ${p}`;
}

function updateSim() {
  const h = parseInt(sHour.value, 10);
  const day = sDay.value;
  const weather = sWeather.value;
  const temp = parseInt(sTemp.value, 10);
  const isHoliday = sHoliday.checked;

  bHour.textContent = formatH(h);
  bTemp.textContent = `${temp} °C (${temp + 273} K)`;

  let base = (day === 'weekday') ? weekdayCurve[h] : weekendCurve[h];
  let modifier = 1.0;
  let weatherText = '0% (clear)';

  switch (weather) {
    case 'clouds': modifier = 0.98; weatherText = '-2% (clouds)'; break;
    case 'rain_light': modifier = 0.92; weatherText = '-8% (light rain)'; break;
    case 'rain_heavy': modifier = 0.82; weatherText = '-18% (heavy rain)'; break;
    case 'snow_light': modifier = 0.85; weatherText = '-15% (snow)'; break;
    case 'snow_heavy': modifier = 0.68; weatherText = '-32% (heavy snow)'; break;
    case 'fog': modifier = 0.90; weatherText = '-10% (fog)'; break;
  }

  if (temp < -15) modifier *= 0.92;
  if (isHoliday) base *= 0.65;

  const vol = Math.round(base * modifier);
  animateNumber(numVol, vol);
  numVol.classList.remove('pulse');
  void numVol.offsetWidth; // restart animation
  numVol.classList.add('pulse');

  bTime.textContent = day === 'weekday'
    ? (h >= 7 && h <= 9 ? 'Morning peak commute' : (h >= 16 && h <= 18 ? 'Evening peak commute' : (h <= 5 ? 'Night flow' : 'Midday traffic')))
    : 'Weekend curve';

  bWeather.textContent = weatherText;
  const capPct = Math.min(100, Math.round((vol / 7280) * 100));
  bCap.textContent = `${capPct}% of highway capacity`;

  let statusClass = 'st-light';
  if (vol > 5500) {
    badgeStatus.textContent = 'Severe congestion / peak rush';
    statusClass = 'st-rush';
  } else if (vol > 3600) {
    badgeStatus.textContent = 'Moderate commute flow';
    statusClass = 'st-mod';
  } else {
    badgeStatus.textContent = 'Light / free-flow traffic';
    statusClass = 'st-light';
  }
  badgeStatus.className = `status-badge ${statusClass}`;
  numVol.style.color = statusClass === 'st-rush' ? '#F2837A' : statusClass === 'st-mod' ? '#F2A900' : '#FFFFFF';
}

function setPreset(h, day, weather, temp, isHol) {
  sHour.value = h;
  sDay.value = day;
  sWeather.value = weather;
  sTemp.value = temp;
  sHoliday.checked = isHol;
  updateSim();
}

[sHour, sDay, sWeather, sTemp, sHoliday].forEach((el) => {
  el.addEventListener('input', updateSim);
  el.addEventListener('change', updateSim);
});
updateSim();

/* ─── Live Minneapolis weather → advisory board ──────────────────── */
(function () {
  const API_KEY = '6f758c1057f74c43b5f163533252311';
  const url = `https://api.weatherapi.com/v1/current.json?key=${API_KEY}&q=Minneapolis&aqi=no`;

  function applyMascotState({ tempC, condText, precipMm, cloudPct }) {
    document.getElementById('mascot-temp').textContent = `${Math.round(tempC)}°C`;
    document.getElementById('mascot-cond').textContent = condText.toUpperCase();
    document.getElementById('mascot-rain').textContent = `${precipMm} mm`;
    document.getElementById('mascot-cloud').textContent = `${cloudPct}%`;

    const impact = document.getElementById('mascot-impact');
    const car = document.getElementById('mascot-car');
    let speed = '3.2s'; // free flow, brisk drive

    if (precipMm > 2 || condText.toLowerCase().includes('snow')) {
      impact.textContent = 'Heavy drag (-20%)';
      impact.style.color = '#F2837A';
      speed = '7s';
    } else if (cloudPct > 75) {
      impact.textContent = 'Slight slowdown';
      impact.style.color = '#F2A900';
      speed = '4.5s';
    } else {
      impact.textContent = 'Clear, smooth flow';
      impact.style.color = '#5FCB94';
      speed = '3.2s';
    }

    if (car) {
      car.style.animation = `driveAcross ${speed} linear infinite`;
    }
  }

  // inject the drive keyframes once
  const styleTag = document.createElement('style');
  styleTag.textContent = `
    #mascot-car { animation: driveAcross 3.2s linear infinite; transform-box: fill-box; }
    @keyframes driveAcross {
      0% { transform: translateX(0); }
      100% { transform: translateX(238px); }
    }
    #mascot-cloud { animation: bobCloud 5s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
    @keyframes bobCloud {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-4px); }
    }
  `;
  document.head.appendChild(styleTag);

  fetch(url)
    .then((r) => r.json())
    .then((data) => {
      const cur = data.current;
      applyMascotState({
        tempC: cur.temp_c,
        condText: cur.condition.text,
        precipMm: cur.precip_mm,
        cloudPct: cur.cloud
      });
    })
    .catch(() => {
      applyMascotState({ tempC: 22, condText: 'Clear', precipMm: 0, cloudPct: 10 });
    });
})();