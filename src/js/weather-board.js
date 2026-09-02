/* ============================================================
   js/weather-board.js
   Live Minneapolis weather → VMS advisory board in the hero section
   ============================================================ */

(function initWeatherBoard() {
  const API_KEY = '6f758c1057f74c43b5f163533252311';
  const API_URL = `https://api.weatherapi.com/v1/current.json?key=${API_KEY}&q=Minneapolis&aqi=no`;

  // ── Inject SVG animation keyframes once ─────────────────────
  const styleTag = document.createElement('style');
  styleTag.textContent = `
    #mascot-car {
      animation: driveAcross 3.2s linear infinite;
      transform-box: fill-box;
    }
    @keyframes driveAcross {
      0%   { transform: translateX(0);     }
      100% { transform: translateX(238px); }
    }
    #mascot-cloud {
      animation: bobCloud 5s ease-in-out infinite;
      transform-box: fill-box;
      transform-origin: center;
    }
    @keyframes bobCloud {
      0%, 100% { transform: translateY(0);    }
      50%      { transform: translateY(-4px); }
    }
  `;
  document.head.appendChild(styleTag);

  // ── Determine car animation speed by conditions ─────────────
  /**
   * @param {{ tempC: number, condText: string, precipMm: number, cloudPct: number }} state
   */
  function applyMascotState({ tempC, condText, precipMm, cloudPct }) {
    const setText = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setText('mascot-temp',      `${Math.round(tempC)}°C`);
    setText('mascot-cond',      condText.toUpperCase());
    setText('mascot-rain',      `${precipMm} mm`);
    setText('mascot-cloud-val', `${cloudPct}%`);

    // Impact label + car speed
    const impact = document.getElementById('mascot-impact');
    const car    = document.getElementById('mascot-car');

    let speed, impactText, impactColor;

    if (precipMm > 2 || condText.toLowerCase().includes('snow')) {
      impactText  = 'Heavy drag (-20%)';
      impactColor = '#F2837A';
      speed       = '7s';
    } else if (cloudPct > 75) {
      impactText  = 'Slight slowdown';
      impactColor = '#F2A900';
      speed       = '4.5s';
    } else {
      impactText  = 'Clear, smooth flow';
      impactColor = '#5FCB94';
      speed       = '3.2s';
    }

    if (impact) {
      impact.textContent = impactText;
      impact.style.color = impactColor;
    }
    if (car) {
      car.style.animation = `driveAcross ${speed} linear infinite`;
    }
  }

  // ── Fetch live weather ───────────────────────────────────────
  fetch(API_URL)
    .then(r => r.json())
    .then(data => {
      const cur = data.current;
      applyMascotState({
        tempC:    cur.temp_c,
        condText: cur.condition.text,
        precipMm: cur.precip_mm,
        cloudPct: cur.cloud,
      });
    })
    .catch(() => {
      // Graceful fallback: clear sunny day
      applyMascotState({ tempC: 22, condText: 'Clear', precipMm: 0, cloudPct: 10 });
    });
})();
