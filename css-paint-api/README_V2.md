```js
registerPainter('something', class extends ElementPainter {
  visualOverflow(geometry, styleMap) {
    return {
      // Size of overflow.
    };
  }
  
  drawBackground(ctx, geometry, styleMap) {
    ctx.save();
    ctx.globalAlpha = 0.5; // Local to just the background layer, are there other canvas ctx params which 
    super(ctx, geom, styleMap);
    ctx.restore();
    ctx.draw(styleMap.get('--other-background-image'));
  }
  
  configureBackgroundContext(ctx, geometry, styleMap) {
    ctx.clipPath = new Path2D(); // ctx here would be subset that could be describing imperitively.
  }

  drawBorder(ctx, geometry, styleMap) {
  
  }
  
  configureBorderContext(ctx, geometry, styleMap) {
    ctx.clipPath = new Path2D(); // ctx here would be subset that could be describing imperitively.
  }
  
  drawForeground(ctx, geometry, styleMap) { // TODO add issue for this callback, use cases.
    ctx.drawImage(styleMap.get('--something-in-content-layer'));
    
    super(ctx, geometry, styleMap);
    
    ctx.drawImage(styleMap.get('--something-in-content-layer'));
  }
  
  configureForegroundContext(ctx, geometry, styleMap) {
    ctx.clipPath = new Path2D(); // ctx here would be subset that could be describing imperitively.
  }
  
  // still need this as creates stacking context.
  configureContext(ctx, geometry, styleMap) {
    ctx.clipPath = new Path2D(); // ctx here would be subset that could be describing imperitively.
  }
});
```

```css
.class {
  painter: something; // implies this creates a stacking context.
}
```


```js
PaintV2RenderingContext.drawImage(styleMap.get('background-image'), ....);
PaintV2RenderingContext.opacity
PaintV2RenderingContext.clipPath = Path2D
PaintV2RenderingContext.filter = styleMap.get('--filter-type'); or 'blur(2px)';

```
