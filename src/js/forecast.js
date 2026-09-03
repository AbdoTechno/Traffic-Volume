/* ============================================================
   js/forecast.js
   Production Forecast — hour-range picker, API call, rendering
   ============================================================ */

// ── DOM references ────────────────────────────────────────────
const prodStartDate  = document.getElementById('prod-start-date');
const prodDays       = document.getElementById('prod-days');
const prodCity       = document.getElementById('prod-city');
const prodStartHour  = document.getElementById('prod-start-hour');
const prodEndHour    = document.getElementById('prod-end-hour');
const prodCurrentVolume = document.getElementById('prod-current-volume');
const prodOutput     = document.getElementById('prod-output');
const prodSubmit     = document.getElementById('prod-submit');
const prodStatusChip = document.getElementById('prod-status-chip');

const startHourVal  = document.getElementById('start-hour-val');
const endHourVal    = document.getElementById('end-hour-val');
const hourRangeDisp = document.getElementById('hour-range-display');
const hourRangeFill = document.getElementById('hour-range-fill');

// ── Helpers ───────────────────────────────────────────────────
/**
 * Format an integer hour as "HH:00" (24-hour, zero-padded).
 * @param {number} h
 * @returns {string}
 */
function fmtHour(h) {
  return `${String(h).padStart(2, '0')}:00`;
}

/**
 * Return a traffic-level label and CSS class based on volume.
 * @param {number} vol  vehicles/hr
 * @returns {{ label: string, cls: string }}
 */
function trafficLevel(vol) {
  if (vol >= 5500) return { label: 'Heavy',    cls: 'level-heavy'  };
  if (vol >= 3500) return { label: 'Moderate', cls: 'level-mod'    };
  if (vol >= 1500) return { label: 'Normal',   cls: 'level-normal' };
  return               { label: 'Light',    cls: 'level-light'  };
}

/**
 * Convert a volume to a bar-chart percentage (max = 7280 veh/hr).
 * @param {number} vol
 * @returns {number}  0–100
 */
function barWidth(vol) {
  return Math.min(100, Math.round((vol / 7280) * 100));
}

/**
 * Determine API base URL.
 * When loaded via VS Code Live Server (port 5500) or file://, target FastAPI on port 8000.
 * In normal deployment or same-port testing, use same-origin relative path.
 */
function getApiBaseUrl() {
  if (window.location.port === '5500' || window.location.protocol === 'file:') {
    return 'http://127.0.0.1:8000';
  }
  return '';
}

// ── Hour-range slider UI ──────────────────────────────────────
function updateHourRange() {
  let s = parseInt(prodStartHour.value, 10);
  let e = parseInt(prodEndHour.value, 10);

  // Clamp: end must be >= start
  if (e < s) {
    if (this === prodEndHour) { prodStartHour.value = s = e; }
    else                      { prodEndHour.value   = e = s; }
  }

  if (startHourVal)  startHourVal.textContent  = fmtHour(s);
  if (endHourVal)    endHourVal.textContent    = fmtHour(e);
  if (hourRangeDisp) hourRangeDisp.textContent = `${fmtHour(s)} → ${fmtHour(e)}`;

  if (hourRangeFill) {
    const pct = h => (h / 23) * 100;
    hourRangeFill.style.left  = `${pct(s)}%`;
    hourRangeFill.style.width = `${pct(e) - pct(s)}%`;
  }
}

// Set today's date as default value
if (prodStartDate) {
  const today     = new Date();
  const localISO  = new Date(today.getTime() - today.getTimezoneOffset() * 60000)
    .toISOString().slice(0, 10);
  prodStartDate.value = localISO;
}

// Wire up hour sliders
if (prodStartHour) {
  prodStartHour.addEventListener('input', updateHourRange);
  prodEndHour.addEventListener('input',   updateHourRange);
  updateHourRange.call(prodStartHour); // initial render
}

// ── HTML renderers ────────────────────────────────────────────
/**
 * Render an inline warning block.
 * @param {string} msg
 * @param {string} [advice]
 * @returns {string} HTML string
 */
function renderWarning(msg, advice = '') {
  return `
    <div class="forecast-warning">
      <p>${msg}</p>
      ${advice ? `<small>${advice}</small>` : ''}
    </div>`;
}

/**
 * Render a single day card with hourly bar chart.
 * @param {object} day  — one item from API predictions[]
 * @returns {string} HTML string
 */
function renderDayCard(day) {
  const d       = new Date(`${day.date}T12:00:00`);
  const dayName = d.toLocaleDateString('en-US', { weekday: 'long' });
  const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  const avgLvl  = trafficLevel(day.daily_avg);
  const peakLvl = trafficLevel(day.peak_volume);
  const modelBadge = day.primary_model === 'AutoRegressive Lag-XGBoost'
    ? '<span class="role-badge role-targ" style="font-size:10px; margin-left:6px;">AutoRegressive TS</span>'
    : '<span class="role-badge role-feat" style="font-size:10px; margin-left:6px;">Tabular XGBoost</span>';

  const hourlyRows = day.hourly.map(h => {
    const lvl = trafficLevel(h.predicted_traffic_volume);
    const w   = barWidth(h.predicted_traffic_volume);
    return `
      <div class="hourly-row">
        <span class="hourly-time">${fmtHour(h.hour)}</span>
        <div class="hourly-bar-wrap">
          <div class="hourly-bar ${lvl.cls}" style="width:${w}%"></div>
        </div>
        <span class="hourly-vol">${Math.round(h.predicted_traffic_volume).toLocaleString()}</span>
      </div>`;
  }).join('');

  return `
    <div class="day-card">
      <div class="day-card-header">
        <div class="day-card-date">
          <strong>${dayName}</strong>
          <span>${dateStr}</span>
          ${modelBadge}
        </div>
        <div class="day-card-avg">
          <div class="day-avg-val">${Math.round(day.daily_avg).toLocaleString()}</div>
          <div class="day-avg-label">avg veh/hr</div>
        </div>
        <span class="level-chip ${avgLvl.cls}">${avgLvl.label}</span>
      </div>

      <div class="day-peak-row">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
          <polyline points="17 6 23 6 23 12"/>
        </svg>
        Peak at <strong>${fmtHour(day.peak_hour)}</strong>
        — ${Math.round(day.peak_volume).toLocaleString()} veh/hr
        <span class="peak-chip ${peakLvl.cls}">${peakLvl.label}</span>
      </div>

      <div class="hourly-bars">${hourlyRows}</div>
    </div>`;
}

/**
 * Render the complete forecast result panel.
 * @param {object} data  — full API response
 */
function renderForecast(data) {
  const days = data.predictions || [];
  if (!days.length) {
    prodOutput.innerHTML = '<p class="prod-no-data">No forecast data returned.</p>';
    return;
  }

  const rangeLabel = `${fmtHour(data.start_hour)} – ${fmtHour(data.end_hour)}`;

  prodOutput.innerHTML = `
    <div class="forecast-meta">
      <div class="forecast-meta-city">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
        ${data.city}
      </div>
      <div class="forecast-meta-range">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        ${rangeLabel} · ${data.days} day${data.days > 1 ? 's' : ''}
      </div>
    </div>
    <div class="forecast-days">
      ${days.map(renderDayCard).join('')}
    </div>`;
}

// ── API call ──────────────────────────────────────────────────
async function fetchProductionForecast() {
  if (!prodStartDate || !prodDays || !prodCity || !prodOutput) return;

  const startH = parseInt(prodStartHour.value, 10);
  const endH   = parseInt(prodEndHour.value,   10);

  if (endH < startH) {
    prodOutput.innerHTML = renderWarning(
      'Invalid hour range',
      'End hour must be greater than or equal to start hour.',
    );
    return;
  }

  const payload = {
    start_date: prodStartDate.value,
    days:       Number(prodDays.value || 1),
    city:       prodCity.value || 'Minneapolis',
    country:    'US',
    start_hour: startH,
    end_hour:   endH,
  };

  if (prodCurrentVolume && prodCurrentVolume.value.trim() !== '') {
    const parsedVol = parseFloat(prodCurrentVolume.value.trim());
    if (!isNaN(parsedVol) && parsedVol >= 0) {
      payload.current_volume = parsedVol;
    }
  }

  // Loading state
  prodSubmit.disabled = true;
  prodSubmit.innerHTML = `<span class="spinner"></span> Fetching…`;
  prodOutput.innerHTML = `
    <div class="prod-loading">
      <span class="spinner spinner-lg"></span>
      <p>Fetching forecast…</p>
    </div>`;
  if (prodStatusChip) prodStatusChip.textContent = '';

  try {
    const apiUrl = `${getApiBaseUrl()}/predict`;
    const response = await fetch(apiUrl, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    if (!response.ok) {
      let msg = 'Forecast unavailable.';
      try {
        const errData = await response.json();
        msg = typeof errData.detail === 'string'
          ? errData.detail
          : (errData.detail?.[0]?.msg ?? msg);
      } catch (_) {}
      throw new Error(msg);
    }

    const data = await response.json();
    renderForecast(data);

    if (prodStatusChip) {
      const n = data.predictions.length;
      prodStatusChip.textContent = `✓ ${n} day${n > 1 ? 's' : ''} · ${data.start_hour}–${data.end_hour}h`;
      prodStatusChip.className   = 'prod-output-status status-ok';
    }
  } catch (error) {
    let userMessage = error.message || 'Failed to fetch forecast';
    let advice = '';

    if (userMessage.includes('days') || userMessage.includes('less than')) {
      userMessage = ' Maximum 3 days allowed';
      advice      = 'Please select 3 days or fewer.';
    } else if (userMessage.includes('accessible') || userMessage.includes('fetch') || userMessage.includes('Failed to fetch')) {
      userMessage = 'API connection failed';
      advice      = window.location.port === '5500'
        ? 'Running with Live Server: Please ensure the FastAPI backend is running via `uvicorn app.main:app` on port 8000.'
        : 'The backend server is temporarily unavailable.';
    } else if (userMessage.includes('weather') || userMessage.includes('forecast')) {
      userMessage = 'Weather data unavailable';
      advice      = 'Unable to fetch weather forecast for the selected city.';
    }

    prodOutput.innerHTML = renderWarning(userMessage, advice);
    if (prodStatusChip) {
      prodStatusChip.textContent = 'Error';
      prodStatusChip.className   = 'prod-output-status status-err';
    }
  } finally {
    prodSubmit.disabled = false;
    prodSubmit.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2.5">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg> Get Forecast`;
  }
}

// ── Wire up submit button ────────────────────────────────────
if (prodSubmit) {
  prodSubmit.addEventListener('click', fetchProductionForecast);
}

// ── 2018 Benchmark Preset Applicator ─────────────────────────
function applyForecastPreset(dateStr, startH, endH, sensorVal) {
  if (dateStr) {
    prodStartDate.value = dateStr;
  } else {
    const now = new Date();
    prodStartDate.value = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
      .toISOString().slice(0, 10);
  }
  prodDays.value = 1;
  prodStartHour.value = startH;
  prodEndHour.value = endH;
  updateHourRange.call(prodStartHour);
  if (prodCurrentVolume) {
    prodCurrentVolume.value = sensorVal !== null && sensorVal !== undefined ? sensorVal : '';
  }
  fetchProductionForecast();
}
window.applyForecastPreset = applyForecastPreset;

