registerPaint('circle', class {
	static get inputProperties() { return ['--circle-color']; }
	paint(ctx, geom, properties) {
		// Change the fill color.
		const color = properties.get('--circle-color');
		ctx.fillStyle = color.cssText;

		// Determine the center point and radius.
		const x = geom.width / 2;
		const y = geom.height / 2;
		const radius = Math.min(x, y);

		// Draw the circle \o/
		ctx.beginPath();
		ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
		ctx.fill();
	}
});
