CSS Paint API Explained
=======================

The CSS Paint API is being developed to improve the extensibility of CSS.

Specifically this allows developers to write a paint function which allows us to draw directly into
an elements background, border, or content.

This work was motivated for a couple of reasons:

### Reduction of DOM ###

We noticed that developers are using an increasing amount of DOM to create visual effects. As an
example the [&lt;paper-button&gt;](https://www.webcomponents.org/element/PolymerElements/paper-button/paper-button)
uses multiple divs to achieve the "ripple" effect.

Instead of using addition divs the developer could just draw directly into the background-image of
the element instead.

This means that the memory and cpu usage of the page would go down, the rendering engine doesn't
have to keep in memory the additional DOM nodes, in addition to performing style-recalc, layout,
painting for all these additional divs.

### Efficiency Gains ###

Providing a "hook" into the rendering engine allows for efficiency gains which are difficult to
achieve with current APIs.

#### Invalidation ####

As the CSS paint API Invalidation is based off style changes, this check can occur in the same pass
as the rest of the box tree. For example:

```css
my-button {
    --property-which-invalidates-paint: no-hover;
}

my-button:hover {
    --property-which-invalidates-paint: hover;
}
```

To achieve the same effect with current APIs you have to rebuild the engines invalidation logic
which is potentially less efficient.

#### Painting ####

Once a box has been invalidated, a rendering engine isn't required to paint it that frame. For
example some rendering engines just paint what is visible within the "visual viewport". This means
that only a smaller amount of work is needed to be done.

A naive implementation with existing APIs may try and paint everything within the document.

### Extensibility of CSS ###

We believe that allowing developers to extend CSS is good for the ecosystem. As an example if a
developer wanted an additional feature they could implement it themselves. E.g. if the developer
wanted a new type of dashed border, they shouldn't have to wait for browsers to implement this.

They should have the power to implement this themselves with the same capability as the rendering
engine.

Getting Started
---------------

First you'll need to add a module script into the paint worklet.

```js
if ('paintWorklet' in CSS) {
  await CSS.paintWorklet.addModule('my-paint-script.js');
  console.log('paint script installed!');
}
```

See the worklets explainer for a more involved explaination of worklets. In short worklets:
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
 
The `style` is a Typed-OM style map. It will _only_ contain the CSS properties that you listed under
the static `inputProperties` accessor.

This is to allow the engine to cache results of your paint class. For example if
`--some-other-property` changes the user-agent knows that this doesn't affect your paint class, and
can re-use the stored result.

The only time when your paint class _must_ be called is when the element it is painting into is
within the viewport, and the size or CSS input properties have changed.

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

class BorderRectPainter extends RectPainter {
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

Classes also give the developer a specific point in time to perform pre-initialization work. As an
example:

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

In this example `performPathPreInit` is doing CPU intensive work which should only be done once.
Without classes this would typically be done when the script is first run, instead this is performed
when the class instance is first created (which may be much later in time).

Drawing Images
--------------

The API works in conjunction with the [CSS Properties and Values](https://drafts.css-houdini.org/css-properties-values-api/)
proposal and the [CSS Typed OM](https://drafts.css-houdini.org/css-typed-om/) proposal.

Using the Properties and Values `registerProperty` method, developers can create a custom CSS
property with the `<image>` type. E.g.

```js
registerProperty({
  name: '--profile-image',
  syntax: '<image>'
});
```

This tells the rendering engine to treat the CSS property `--profile-image` as an image; and as a
result the style engine will parse and begin loading that image.

You can then directly draw this image from within your paint method:

```js
registerPaint('avatar', class {
  static inputProperties = ['--profile-image'];
  
  paint(ctx, size, styleMap) {
    // Determine the center point and radius.
    const x = size.width / 2;
    const y = size.height / 2;
    const radius = Math.min(x, y);
    
    ctx.save();
    // Set up a round clipping path for the profile image.
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
    ctx.clip();
    
    // Draw the image inside the round clip.
    ctx.drawImage(styleMap.get('--profile-image'));
    ctx.restore();
    
    // Draw a badge or something on top of the image.
    drawBadge(ctx);
  }
});
```

The above example would be used in CSS by:
```css
.avatar-img {
  background: paint(avatar);
  --profile-image: url("profile-image.png");
}
```

Paint Arguments
---------------

It is also possible with this API to have additional arguments to the `paint()` function, for
example:

```js
registerPaint('circle-args', class {
  static inputArguments = ['<color>'];

  paint(ctx, size, _, args) {
    const color = args[0].cssText;
    ctx.fillStyle = color;

    const x = size.width / 2;
    const y = size.height / 2;
    const radius = Math.min(x, y);

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
    ctx.fill();
  }
});
```

```js
my-element {
  background:
    paint(circle-args, red) center/50% no-repeat,
    paint(cirlce-args, blue);
}
```
