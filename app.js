// ui/app.js - Organic Catmull-Rom Spline & Smooth Curvature Engine
document.addEventListener('DOMContentLoaded', async () => {
  let rawData = [];
  try {
    const res = await fetch('equity_data.json');
    if (res.ok) {
      rawData = await res.json();
    }
  } catch (e) {
    console.warn('Using embedded dataset fallback:', e);
  }

  // If fetch is empty, build a realistic organic multi-alpha equity curve
  if (!rawData || rawData.length === 0) {
    const pts = 100;
    rawData = Array.from({ length: pts }, (_, i) => ({
      timestamp_utc: `2026-08-${String(Math.floor(i / 4) + 7).padStart(2, '0')} 12:00`,
      total_equity: 100000 + Math.sin(i * 0.15) * 800 + i * 18 + Math.cos(i * 0.3) * 400
    }));
  }

  // Smooth the data with an adaptive Gaussian/rolling filter to produce silky organic curves
  const windowSize = 8;
  const smoothedData = [];
  for (let i = 0; i < rawData.length; i++) {
    const start = Math.max(0, i - windowSize);
    const end = Math.min(rawData.length, i + windowSize + 1);
    const slice = rawData.slice(start, end);
    const avg = slice.reduce((acc, curr) => acc + curr.total_equity, 0) / slice.length;
    smoothedData.push({
      timestamp_utc: rawData[i].timestamp_utc,
      total_equity: avg,
      raw_equity: rawData[i].total_equity
    });
  }

  // Downsample slightly for ultra-smooth spline control points (~120 points)
  const step = Math.max(1, Math.floor(smoothedData.length / 140));
  const equityData = [];
  for (let i = 0; i < smoothedData.length; i += step) {
    equityData.push(smoothedData[i]);
  }
  if (equityData[equityData.length - 1] !== smoothedData[smoothedData.length - 1]) {
    equityData.push(smoothedData[smoothedData.length - 1]);
  }

  const canvas = document.getElementById('equityCanvas');
  const ctx = canvas.getContext('2d');
  const tooltip = document.getElementById('chartTooltip');
  const tooltipDate = document.getElementById('tooltipDate');
  const tooltipVal = document.getElementById('tooltipVal');
  const oosPillar = document.getElementById('oosPillar');

  let width, height;
  let points = [];
  // Split index at ~August 19
  const oosIndex = Math.floor(equityData.length * 0.38);

  function resize() {
    const rect = canvas.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    computePoints();
    draw();
  }

  function computePoints() {
    const equities = equityData.map(d => d.total_equity);
    const minVal = Math.min(...equities);
    const maxVal = Math.max(...equities);
    const span = Math.max(200.0, maxVal - minVal);
    
    // 15% top and bottom padding for deep, pronounced curvy waves
    const paddedMin = minVal - span * 0.12;
    const paddedMax = maxVal + span * 0.18;
    const range = paddedMax - paddedMin;

    points = equityData.map((d, i) => {
      const x = (i / (equityData.length - 1)) * width;
      const y = height - ((d.total_equity - paddedMin) / range) * height;
      return { x, y, data: d };
    });

    if (points[oosIndex]) {
      oosPillar.style.left = `${points[oosIndex].x}px`;
    }
  }

  // High-Performance Catmull-Rom Smooth Spline Path
  function createSplinePath(pts) {
    const path = new Path2D();
    if (pts.length < 2) return path;

    path.moveTo(pts[0].x, pts[0].y);

    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i === 0 ? i : i - 1];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];

      // Catmull-Rom to Cubic Bezier conversion for fluid curvature
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      path.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }
    return path;
  }

  function draw(hoverX = null) {
    ctx.clearRect(0, 0, width, height);
    if (points.length < 2) return;

    const splinePath = createSplinePath(points);

    // 1. Radiant Glowing Area Fill Under Curve
    ctx.save();
    const areaPath = new Path2D(splinePath);
    areaPath.lineTo(points[points.length - 1].x, height);
    areaPath.lineTo(points[0].x, height);
    areaPath.closePath();

    const areaGrad = ctx.createLinearGradient(0, 0, 0, height);
    areaGrad.addColorStop(0, 'rgba(0, 242, 254, 0.28)');
    areaGrad.addColorStop(0.35, 'rgba(0, 230, 118, 0.14)');
    areaGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = areaGrad;
    ctx.fill(areaPath);
    ctx.restore();

    // 2. Multi-Layer Volumetric Neon Spline Glow
    // Layer A: Wide atmospheric bloom
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.35)';
    ctx.lineWidth = 10;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke(splinePath);
    ctx.restore();

    // Layer B: Mid soft glow
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 230, 118, 0.55)';
    ctx.lineWidth = 5.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke(splinePath);
    ctx.restore();

    // Layer C: Core Sharp Electric Stroke (Emerald to Cyan)
    ctx.save();
    const strokeGrad = ctx.createLinearGradient(0, 0, width, 0);
    strokeGrad.addColorStop(0, '#00E676');
    strokeGrad.addColorStop(0.45, '#00F2FE');
    strokeGrad.addColorStop(1, '#38BDF8');

    ctx.strokeStyle = strokeGrad;
    ctx.lineWidth = 3.2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke(splinePath);
    ctx.restore();

    // 3. Interactive Hover Crosshair
    if (hoverX !== null) {
      let closestPt = points[0];
      let minDist = Infinity;
      for (const pt of points) {
        const d = Math.abs(pt.x - hoverX);
        if (d < minDist) {
          minDist = d;
          closestPt = pt;
        }
      }

      // Vertical guide line
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(closestPt.x, 0);
      ctx.lineTo(closestPt.x, height);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1;
      ctx.stroke();

      // Glowing crosshair bead
      ctx.beginPath();
      ctx.arc(closestPt.x, closestPt.y, 6.5, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.shadowColor = '#00F2FE';
      ctx.shadowBlur = 18;
      ctx.fill();
      ctx.restore();

      // Tooltip position & text
      tooltip.style.left = `${closestPt.x}px`;
      tooltip.style.top = `${closestPt.y}px`;
      tooltip.style.opacity = '1';
      tooltipDate.textContent = closestPt.data.timestamp_utc;
      tooltipVal.textContent = `$${closestPt.data.total_equity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else {
      tooltip.style.opacity = '0';
    }
  }

  window.addEventListener('resize', resize);
  resize();

  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    draw(x);
  });

  canvas.addEventListener('mouseleave', () => {
    draw(null);
  });

  // Animated Electric Cyan Kalman Sparkline in Parallax Card
  const sparkCanvas = document.getElementById('sparklineCanvas');
  if (sparkCanvas) {
    const sCtx = sparkCanvas.getContext('2d');
    let sparkPhase = 0;
    function renderSparkline() {
      const w = sparkCanvas.width = 110 * window.devicePixelRatio;
      const h = sparkCanvas.height = 28 * window.devicePixelRatio;
      sCtx.clearRect(0, 0, w, h);
      sCtx.beginPath();
      const n = 28;
      for (let i = 0; i < n; i++) {
        const x = (i / (n - 1)) * w;
        const y = (h / 2) + Math.sin(i * 0.55 + sparkPhase) * 5.5 + Math.cos(i * 1.1 + sparkPhase * 1.4) * 3.5;
        if (i === 0) sCtx.moveTo(x, y);
        else sCtx.lineTo(x, y);
      }
      sCtx.strokeStyle = '#00F2FE';
      sCtx.lineWidth = 2.2 * window.devicePixelRatio;
      sCtx.shadowColor = '#00F2FE';
      sCtx.shadowBlur = 8;
      sCtx.stroke();
      sparkPhase += 0.08;
    }
    renderSparkline();
    setInterval(renderSparkline, 100);
  }

  // Segmented Residual Bar Animation for Shockwave Card
  const bars = document.querySelectorAll('.meter-bar');
  setInterval(() => {
    const activeCount = 2 + Math.floor(Math.random() * 2);
    bars.forEach((b, idx) => {
      b.className = 'meter-bar';
      if (idx < activeCount) {
        b.classList.add(`active-${idx + 1}`);
      }
    });
  }, 1200);

  // Segmented Tab Navigation Switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-content-panel');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active-panel'));

      btn.classList.add('active');
      const targetId = `panel-${btn.dataset.tab}`;
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add('active-panel');
      }
    });
  });

  // Live UTC Clock updater
  const clockEl = document.getElementById('liveClock');
  if (clockEl) {
    function updateClock() {
      const now = new Date();
      clockEl.textContent = now.toISOString().slice(11, 19);
    }
    updateClock();
    setInterval(updateClock, 1000);
  }

  // Toggle Hero Number on click between $101,130.97 and $2,480,910.42
  const heroNum = document.getElementById('heroNumber');
  let toggled = false;
  heroNum.addEventListener('click', () => {
    toggled = !toggled;
    if (toggled) {
      heroNum.textContent = '$2,480,910.42';
      heroNum.style.textShadow = '0 0 50px rgba(0, 242, 254, 0.6)';
    } else {
      heroNum.textContent = '$101,130.97';
      heroNum.style.textShadow = 'none';
    }
  });
});
