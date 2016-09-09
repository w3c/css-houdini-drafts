CSS Paint API Explained
=======================

The CSS Paint API is being developered to improve the extensibility of CSS.

Specifically


Getting Started
---------------

First you'll need to import a script into the paint worklet.

```js
if ('paintWorklet' in window) {
  window.paintWorklet.import('my-paint-script.js').then(() => {
    console.log('paint script installed!');
  }
}
```

See the worklets explainer for a more involed explaination of worklets. In short worklets:
 - Are similar to workers in that the script runs in a separate global script context.
 - A script inside a worklet has no DOM, Network, Database, etc access.
 - The global script context lifetime is not defined (you should expect the script context to be killed at any point).
 - May have multiple copies of the script context spawned on multiple CPU cores.

As a couple of concrete example as to how the user agent may use these capabilities:
 - When a "tab" is backgrounded the script context(s) of the paint worklet may be killed to free up memory.
 - A multi-threaded user-engine may spawn multiple backing script contexts to perform the paint phase of the rendering engine in parallel.

Painting a circle
-----------------

The global script context of the paint worklet has exactly one method exposed to developers: `registerPaint`.

```js
registerPaint('circle', class {
  static inputProperties = ['--circle-color'];
  
  paint(ctx, size, style) {
    // Change the fill color.
    const color = style.get('--circle-color');
    ctx.fillStyle = color;

    // Determine the center point and radius.
    const x = size.width / 2;
    const y = size.height / 2;
    const radius = Math.min(x, y);

    // Draw the circle \o/
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
    ctx.fill();
  }
});
```

There are a few things going on in this example so lets step through them one-by-one.

The `paint` function is your callback into the browsers paint phase in the rendering engine. You are given:
 - `ctx`, a rendering context, similar to a `CanvasRenderingContext2D`.
 - `size`, the size of the area in which you should paint.
 - `style`, the computed style of the element which are you currently painting.
 
The `style` is a Typed-OM style map. It will _only_ contain the CSS properties that you listed under the static `inputProperties` accessor.

This is to allow the engine to cache results of your paint class. For example if `--some-other-property` changes the user-agent knows that this doesn't affect your paint class, and can re-use the stored result.

The only time when your paint class _must_ be called is when the element it is painting into is within the viewport, and the size or CSS input properties have changed.

Why classes?
------------

Classes allow composition of paint handlers. As an example:

```js
class RectPainter {
  static inputProperties = ['--rect-color'];
  
  paint(ctx, size, style) {
    // Change the fill color.
    ctx.fillStyle = style.get('--circle-color');

    // Draw the solid rect.
    ctx.fillRect(0, 0, size.width, size.height);
  }
}

class BorderRectPainter {
  static inputProperties = ['--border-color', ...super.inputProperties];
  
  paint(ctx, size, style) {
    super.paint(ctx, size, style);
    
    ctx.strokeStyle = style.get('--border-color');
    ctx.lineWidth = 4;
    
    ctx.strokeRect(0, 0, size.width, size.height);
  }
}

registerPaint('border-rect', BorderRectPainter);
```

Classes also give the developer a specific point in time to perform pre-initialization work. As an example:

```js
registerPaint('lots-of-paths', class {

  constructor() {
    this.paths = performPathPreInit();
  }
  
  performPathPreInit() {
    // Lots of work here to produce list of Path2D object to be reused.
  }
  
  paint(ctx, size, style) {
    ctx.stroke(this.paths[i]); 
  }
});
```

In this example `performPathPreInit` is doing CPU intensive work which should only be done once. Without classes this would typically be done when the script is first run, instead this is performed when the class instance is first created (which may be much later in time).

Drawing Images
--------------

TODO

Paint Efficiency
----------------

TODO
