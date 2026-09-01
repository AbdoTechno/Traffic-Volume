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
  let weatherText = '0% (Clear)';

  switch (weather) {
    case 'clouds':
      modifier = 0.98;
      weatherText = '-2% (Clouds)';
      break;
    case 'rain_light':
      modifier = 0.92;
      weatherText = '-8% (Light Rain)';
      break;
    case 'rain_heavy':
      modifier = 0.82;
      weatherText = '-18% (Heavy Rain)';
      break;
    case 'snow_light':
      modifier = 0.85;
      weatherText = '-15% (Snow)';
      break;
    case 'snow_heavy':
      modifier = 0.68;
      weatherText = '-32% (Heavy Snow)';
      break;
    case 'fog':
      modifier = 0.90;
      weatherText = '-10% (Fog)';
      break;
  }

  if (temp < -15) modifier *= 0.92;
  if (isHoliday) base *= 0.65;

  const vol = Math.round(base * modifier);
  numVol.textContent = vol.toLocaleString();

  bTime.textContent = day === 'weekday'
    ? (h >= 7 && h <= 9 ? 'Morning Peak Commute' : (h >= 16 && h <= 18 ? 'Evening Peak Commute' : (h <= 5 ? 'Night Flow' : 'Midday Traffic')))
    : 'Weekend Curve';

  bWeather.textContent = weatherText;
  const capPct = Math.min(100, Math.round((vol / 7280) * 100));
  bCap.textContent = `${capPct}% of highway capacity`;

  if (vol > 5500) {
    badgeStatus.textContent = 'Severe Congestion / Peak Rush';
    badgeStatus.className = 'status-badge st-rush';
  } else if (vol > 3600) {
    badgeStatus.textContent = 'Moderate Commute Flow';
    badgeStatus.className = 'status-badge st-mod';
  } else {
    badgeStatus.textContent = 'Light / Free-Flow Traffic';
    badgeStatus.className = 'status-badge st-light';
  }
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

(function () {
  const API_KEY = '6f758c1057f74c43b5f163533252311';
  const url = `https://api.weatherapi.com/v1/current.json?key=${API_KEY}&q=Minneapolis&aqi=no`;

  fetch(url)
    .then((r) => r.json())
    .then((data) => {
      const cur = data.current;
      document.getElementById('mascot-temp').textContent = `${Math.round(cur.temp_c)} °C (${Math.round(cur.temp_c + 273.15)} K)`;
      document.getElementById('mascot-cond').textContent = cur.condition.text;
      document.getElementById('mascot-rain').textContent = `${cur.precip_mm} mm`;
      document.getElementById('mascot-cloud').textContent = `${cur.cloud} %`;

      const impact = document.getElementById('mascot-impact');
      if (cur.precip_mm > 2 || cur.condition.text.toLowerCase().includes('snow')) {
        impact.textContent = 'Adverse Weather Drag (-20%)';
        impact.style.color = '#EF4444';
      } else if (cur.cloud > 75) {
        impact.textContent = 'Overcast / Slight Slowdown';
        impact.style.color = '#F59E0B';
      } else {
        impact.textContent = 'Clear & Smooth Flow';
        impact.style.color = '#10B981';
      }
    })
    .catch(() => {
      document.getElementById('mascot-temp').textContent = '22 °C (295 K)';
      document.getElementById('mascot-cond').textContent = 'Clear';
      document.getElementById('mascot-rain').textContent = '0 mm';
      document.getElementById('mascot-cloud').textContent = '10 %';
    });
})();
