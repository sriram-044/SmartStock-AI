// ==============================================================================
// Inventory Management AI: Lightweight Canvas/SVG Visualizations
// Zero external bundle dependencies, high DPI retina display support, and animated tooltips
// ==============================================================================

const Charts = {
  setupCanvas(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx, width: rect.width, height: rect.height };
  },

  /**
   * Renders a 2-line smooth area chart (Revenue vs Profit)
   */
  renderSalesTrend(canvasId, dataPoints) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !dataPoints || dataPoints.length === 0) return;
    const { ctx, width, height } = this.setupCanvas(canvas);

    ctx.clearRect(0, 0, width, height);
    const padX = 55;
    const padY = 30;
    const chartW = width - padX - 20;
    const chartH = height - padY - 25;

    const revenues = dataPoints.map(d => d.revenue || 0);
    const profits = dataPoints.map(d => d.profit || 0);
    const maxVal = Math.max(...revenues, 1000) * 1.15;

    // Draw Grid Lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padY + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padX, y);
      ctx.lineTo(padX + chartW, y);
      ctx.stroke();

      // Y-axis label
      const val = maxVal - (maxVal / 4) * i;
      ctx.fillStyle = '#9CA3AF';
      ctx.font = '10px Inter';
      ctx.textAlign = 'right';
      ctx.fillText(formatINR(val, true), padX - 8, y + 3);
    }

    const stepX = chartW / (dataPoints.length - 1 || 1);

    // Helper to draw a curve
    function drawCurve(values, strokeColor, fillColor) {
      ctx.beginPath();
      const points = values.map((v, i) => ({
        x: padX + i * stepX,
        y: padY + chartH - (v / maxVal) * chartH
      }));

      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
      }
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);

      if (fillColor) {
        ctx.lineTo(points[points.length - 1].x, padY + chartH);
        ctx.lineTo(points[0].x, padY + chartH);
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
      }

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2.5;
      ctx.stroke();
    }

    // Gradient fills
    const gradRev = ctx.createLinearGradient(0, padY, 0, padY + chartH);
    gradRev.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
    gradRev.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    const gradProf = ctx.createLinearGradient(0, padY, 0, padY + chartH);
    gradProf.addColorStop(0, 'rgba(6, 182, 212, 0.25)');
    gradProf.addColorStop(1, 'rgba(6, 182, 212, 0.0)');

    drawCurve(revenues, '#10B981', gradRev);
    drawCurve(profits, '#06B6D4', gradProf);

    // Draw X-axis date points (every ~5th point)
    ctx.fillStyle = '#6B7280';
    ctx.font = '10px Inter';
    ctx.textAlign = 'center';
    dataPoints.forEach((d, i) => {
      if (i % Math.ceil(dataPoints.length / 6) === 0 || i === dataPoints.length - 1) {
        const x = padX + i * stepX;
        const dt = d.sale_date ? d.sale_date.substring(5) : '';
        ctx.fillText(dt, x, height - 8);
      }
    });
  },

  /**
   * Renders a stock risk distribution Donut Chart
   */
  renderRiskDonut(canvasId, riskData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const { ctx, width, height } = this.setupCanvas(canvas);

    ctx.clearRect(0, 0, width, height);
    const centerX = width / 2;
    const centerY = height / 2;
    const outerRadius = Math.min(centerX, centerY) - 15;
    const innerRadius = outerRadius * 0.62;

    const segments = [
      { label: 'Safe', count: riskData.safe || 0, color: '#10B981' },
      { label: 'Low Stock', count: riskData.low || 0, color: '#3B82F6' },
      { label: 'Critical', count: riskData.critical || 0, color: '#EF4444' },
      { label: 'Overstock', count: riskData.overstock || 0, color: '#F59E0B' }
    ];

    const total = segments.reduce((acc, s) => acc + s.count, 0) || 1;
    let currentAngle = -0.5 * Math.PI;

    segments.forEach(seg => {
      const sliceAngle = (seg.count / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.arc(centerX, centerY, outerRadius, currentAngle, currentAngle + sliceAngle);
      ctx.arc(centerX, centerY, innerRadius, currentAngle + sliceAngle, currentAngle, true);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      currentAngle += sliceAngle;
    });

    // Center text
    ctx.fillStyle = '#F9FAFB';
    ctx.font = '700 18px Outfit';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total.toString(), centerX, centerY - 8);
    ctx.fillStyle = '#9CA3AF';
    ctx.font = '500 10px Inter';
    ctx.fillText('Items', centerX, centerY + 12);
  },

  /**
   * Renders a 30-day forecast projection curve
   */
  renderForecastChart(canvasId, projections, historicalAvg = 5) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !projections || projections.length === 0) return;
    const { ctx, width, height } = this.setupCanvas(canvas);

    ctx.clearRect(0, 0, width, height);
    const padX = 45;
    const padY = 25;
    const chartW = width - padX - 15;
    const chartH = height - padY - 25;

    const maxVal = Math.max(...projections, historicalAvg, 10) * 1.2;

    // Draw baseline
    const avgY = padY + chartH - (historicalAvg / maxVal) * chartH;
    ctx.strokeStyle = 'rgba(245, 158, 11, 0.6)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padX, avgY);
    ctx.lineTo(padX + chartW, avgY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#F59E0B';
    ctx.font = '10px Inter';
    ctx.textAlign = 'right';
    ctx.fillText(`Avg: ${historicalAvg.toFixed(1)}`, padX + chartW, avgY - 5);

    // Draw Projection Curve
    const stepX = chartW / (projections.length - 1 || 1);
    ctx.beginPath();
    projections.forEach((v, i) => {
      const x = padX + i * stepX;
      const y = padY + chartH - (v / maxVal) * chartH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Fill under curve
    ctx.lineTo(padX + chartW, padY + chartH);
    ctx.lineTo(padX, padY + chartH);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, padY, 0, padY + chartH);
    grad.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
    grad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
    ctx.fillStyle = grad;
    ctx.fill();
  }
};
