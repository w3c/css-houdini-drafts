registerPaint('chat', class {
  static get inputProperties() { return ['background-image', '--chat-images-num']; }

  constructor() {
    this.radii = [
      0.5,
      1 / (2 + 2/Math.SQRT2),
      0.25,
      0.25,
      1 / Math.SQRT2 - 0.5,
    ];

    const fudge = 0.03349;
    this.positions = [
      [
        {x: 0.5, y: 0.5},
      ],
      [
        {x: this.radii[1], y: this.radii[1]},
        {x: 1-this.radii[1], y: 1-this.radii[1]},
      ],
      [
        {x: 0.5, y: 0.25 + fudge},
        {x: 0.75, y: 0.75 - fudge},
        {x: 0.25, y: 0.75 - fudge},
      ],
      [
        {x: 0.25, y: 0.25},
        {x: 0.75, y: 0.25},
        {x: 0.25, y: 0.75},
        {x: 0.75, y: 0.75},
      ],
      [
        {x: this.radii[4], y: this.radii[4]},
        {x: 1-this.radii[4], y: this.radii[4]},
        {x: 0.5, y: 0.5},
        {x: 1-this.radii[4], y: 1-this.radii[4]},
        {x: this.radii[4], y: 1-this.radii[4]},
      ],
    ];

    this.colors = [
      '#E91E63',
      '#9C27B0',
      '#2196F3',
      '#8BC34A',
      '#FF9800',
    ];
  }

  paint(ctx, geom, styleMap) {
    ctx.fillStyle = '#FFF';
    ctx.fillRect(0, 0, geom.width, geom.height);

    // Chrome can only use background-images as source images at the moment.
    const images = styleMap.getAll('background-image');

    const num = styleMap.get('--chat-images-num').value;
    const num_low = Math.floor(num);
    const num_high = Math.ceil(num);

    const dist = (num - num_low);
    const size = Math.min(geom.width, geom.height);

    const r_low = this.radii[num_low-1];
    const r_high = this.radii[num_high-1];

    const pos_low = this.positions[num_low-1];
    const pos_high = this.positions[num_high-1];

    for (let i = 0; i < num_high; i++) {
      if (!pos_high) break;
      const low = pos_low && pos_low[i];
      const high = pos_high[i];

      let x, y, r;
      if (num_low != num_high && i == num_high - 1) {
        x = size * high.x;
        y = size * high.y;
        r = size * dist * r_high;
      } else {
        x = size * ((1-dist) * low.x + dist * high.x);
        y = size * ((1-dist) * low.y + dist * high.y);
        r = size * ((1-dist) * r_low + dist * r_high);
      }

      ctx.fillStyle = this.colors[i];
      ctx.beginPath();
      ctx.arc(x, y, 0.95 * r, 0, Math.PI*2);
      ctx.fill();

      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, 0.9 * r, 0, Math.PI * 2);
      ctx.clip();
      ctx.drawImage(images[i], x - r, y - r, 2*r, 2*r);
      ctx.restore();
    }
  }
});
