registerPaint('arc', class {
  static get inputArguments() {
    return [
      '<color>',
      '<angle>',  // startAngle
      '<angle>',  // endAngle
      '<length>', // radius
      '<length>', // lineWidth
    ];
  }

  constructor() {
    this.regex = /[a-z]+/g;
  }

  paint(ctx, geom, _, args) {
    ctx.strokeStyle = args[0].cssText;

    // Determine the center point.
		const x = geom.width / 2;
		const y = geom.height / 2;

    // Convert the start and end angles to radians.
    const startAngle = this.convertAngle(args[1]) - Math.PI / 2;
    const endAngle = this.convertAngle(args[2]) - Math.PI / 2;

    // Convert the radius and lineWidth to px.
    const radius = this.convertLength(args[3]);
    const lineWidth = this.convertLength(args[4]);

    ctx.lineWidth = lineWidth;

    ctx.beginPath();
    ctx.arc(x, y, radius, startAngle, endAngle, false);
    ctx.stroke();
  }

  convertAngle(angle) {
    const value = angle.value || parseFloat(angle.cssText);
    const unit = angle.unit || angle.cssText.match(this.regex)[0];

    switch (unit) {
      case 'deg':
        return value * Math.PI / 180;
      case 'rad':
        return value;
      case 'grad':
        return value * Math.PI / 200;
      case 'turn':
        return value * Math.PI / 0.5;
      default:
        throw Error(`Unknown angle unit: ${unit}`);
    }
  }

  convertLength(length) {
    switch (length.type) {
      case 'px':
        return length.value;
      default:
        throw Error(`Unkown length type: ${length.type}`);
    }
  }
});
