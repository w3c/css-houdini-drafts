# Compositor Worker explained

## tl;dr

requestAnimationFrame on the "compositor" thread.

## So, what's the problem here?

Scripted effects (driven by requestAnimationFrame, response to onscroll, etc)
are flexible and powerful, but are subject to main thread jank (where jank
refers to unpredictable interruptions in the rate that animations are serviced
on a thread due to other, unrelated work on that thread). And although script
can run on a web worker, DOM access and CSS property animations are not
permitted. Despite their susceptibility to main thread jank, main thread
animations are widely used; they're the only way to create common effects such
as position-sticky, image carousels, custom scroll animations, iphone-style
contact lists, and physics-based animations. In a perfect world, the main thread
would always be responsive enough to guarantee that an animation callback would
be serviced every frame. In reality, this is often extremely hard to achieve,
both for user agents and developers of large sites composed of disparate, 3rd
party components not under the author's control. The result is a lot of janky
pages.

Why can't we update CSS properties from another thread? Updating CSS properties
could effect a style recalc or a layout and those operations must happen on the
main thread. That said, there are certain 'layout-free' properties that can be
modified without these side effects. These properties include transform,
opacity, background color, background position, etc. Updating the scroll offset
is also layout-free. Clearly identifying these layout-free properties and
allowing them to be animated from a separate scheduling domain would provide a
simple and powerful way to achieve smooth animations.

Indeed, all major browsers have had the ability to asynchronously update
layout-free properties for years. Some examples include WebAnimations, CSS
animations, and transitions involving layout-free properties as well as
compositor driven scrolling. A few new approaches are in the works such as
position:sticky and snap points, but it's unfortunate to have to wait for specs
and consistent browser implementations to get these new "acclerated" effects.

## Goal

Allow new accelerated, input/time-based effects to be authored in script.
Address at least [this](https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/UseCases.md) list of use cases as well as supporting [these scroll customization use cases](https://github.com/w3c/css-houdini-drafts/blob/master/scroll-customization-api/UseCases.md).

## High level approach

 - Introduce CompositorWorker whose global scope exposes requestAnimationFrame
   which runs at the rate of threaded scrolling and animation.
 - Allow DOM elements to be wrapped in a CompositorProxy which may be sent to a
   CompositorWorker and which exposes a limited set of layout-free properties
   and input events.

## A tiny, but expressive kernel

This small set of primitives would permit a surprisingly large number of
existing and proposed browser features to be implemented as polyfills.

 - Portions of [Web Animations](http://dev.w3.org/fxtf/web-animations/)
 - [Touch-based Animation Scrubbing](https://docs.google.com/document/d/1vRUo_g1il-evZs975eNzGPOuJS7H5UBxs-iZmXHux48/edit)
 - [position:sticky](http://updates.html5rocks.com/2012/08/Stick-your-landings-position-sticky-lands-in-WebKit)
 - [Smooth Scrolling](http://dev.w3.org/csswg/cssom-view/), Sections 4, 5, 7, 12, and 13.
 - Accelerated CSS animations. ([I/O talk](http://www.youtube.com/watch?v=hAzhayTnhEI))
 - [Snap Points](https://www.w3.org/TR/css-snappoints-1/)

## Examples

The following examples are written to an API shape that is likely to change in the future. The goal here is to cleary articulate the concepts, not to propose final syntax.

### Example 1. Hello, World!

Here we create a trivial, time-based animation.

Main Thread
```JavaScript
// The list of properties determine which properties may be
// modified on the CompositorWorker.
var proxy = new CompositorProxy(element, ['transform']);

// If a requested property may not modified, then |supports|
// will return false as follows.
console.log('transform may be modified: ' + proxy.supports('transform'));

// The UA is free to drive a CompositorWorker from a thread of its
// choosing, provided it fires requestAnimationFrame callbacks in
// sync with compositor driven scrolling, modulo script exceeding
// frame budget. If, for whatever reason, a CompositorWorker’s
// requested compositor frame callbacks are unable to complete in
// time, the worker’s onerror handler will be called with a
// TimeoutError. See comment below about the application of effects.
// In future, we will almost certainly specify other behaviors when
// the worker’s frame callbacks cannot complete (e.g., kill the
// worker), but the initial behavior will simply be to let the
// effect fall out of sync with other compositor-driven effects.
var worker = new CompositorWorker(‘my_script.js’);
worker.postMessage(proxy);
```
On the CompositorWorker
```JavaScript
onmessage = function(e) {
    var proxy = e.data;
    var tick = function(timestamp) {
        var t = proxy.transform;
        t.m42 = 100.0 * Math.sin(timestamp / 1000.0);
        proxy.transform = t;
        requestAnimationFrame(tick);
    };
    // All requestAnimationFrame callbacks are processed as a unit;
    // their effects will all be applied in the same frame.
    requestAnimationFrame(tick);
};
```
### Example 2. Parallax

Although we could implement parallax by checking the scroll position
every frame, it's more efficient if we only update when we've actually
scrolled. Here's a proposal for how that might look.

Main Thread
```JavaScript
var scroller_proxy = new CompositorProxy(scroller, ['scrollTop']);
var background_proxy = new CompositorProxy(background, ['transform']);
var worker = new CompositorWorker('parallax.js');
worker.postMessage({
  'scroller': scroller_proxy,
  'background': background_proxy
});
```

On the CompositorWorker
```JavaScript
onmessage = function(e) {
  var scroller = e.data.scroller;
  var background = e.data.background;
  var update = function(timestamp) {
    var t = background.transform;
    t.m42 = 0.8 * scroller.scrollTop;
    background.transform = t;
    // In this case, |update| will be called iff a property
    // of scroller's has been updated.
    requestAnimationFrame(update, [scroller]);
  };
  requestAnimationFrame(update, [scroller]);
};
```

### Example 3. Input

This example shows how we might implement a simple drawer. The way input will be provided to a CompositorWorker is very much an open question, so treat the following as speculative and likely to change.

Main Thread
```JavaScript
var drawer_proxy = new CompositorProxy(drawer, [transform]);
var worker = new CompositorWorker('drawer.js');
worker.postMessage(drawer_proxy);
```

On the CompositorWorker
```JavaScript
onmessage = function(e) {
  var drawer = e.data;
  drawer.addEventListener('touchstart', function(e) {
    drawer.initialX = e.touches[0].pageX;
  });
  drawer.addEventListener('touchmove', function(e) {
    var t = drawer.transform;
    t.m41 = e.touches[0].pageX - drawer.initialX;
    drawer.transform = t;
  });
};
```

## Common Concerns

### Are we marrying ourselves to implementation details?

Virtually all user agents support (via CSS) accelerated opacity and transform animations, and they’re going to have to support them for the foreseeable future. Threaded scrolling is also increasingly common. By whatever means browsers are currently able to guarantee that things can slide around, scroll and fade in and out efficiently and asynchronously with respect to the main thread, they will continue to do so in the future. That is, we're not tying ourselves to properties that may cease to be possible to update asynchronously, nor are we tying ourselves to the machinery that makes this asynchronous updating possible. It doesn’t, for example, tie us to the idea of a composited layer or a layer tree, concepts that may not be meaningful in all browser implementations. The animated elements might, say, be redrawn by the GPU each frame. But this doesn’t matter. These implementation details are orthogonal to the animation proxy concept.

### What happens when script runs long?

On some platforms or user agents, it may be unacceptable or impossible to slow down native scrolling. We must have a fallback. There are a number of reasonable failure modes, and one that seems like a natural default.
 * _Default_: Fall out of sync. In this case, the user agent would attempt to retrieve a value from the various CompositorWorker requestAnimationFrame callbacks, but if they have not finished within the frame budget, they will be applied in a subsequent frame, falling out of sync with, say, compositor driven scrolling. When this happens the worker's onerror function will be called with a TimeoutError so that the author has the option to react.
 * Force all compositor-driven effects to the main thread. In this case, the effects will remain synchronized, though they will become susceptible to main thread jank. Again, we would communicate failure via onerror.
 * Abort the effect. I.e., if we cannot keep up with the compositor, do not call requestAnimationFrame for that CompositorWorker again. This would be useful in cases where scroll/animation performance is critical, but the effect is a nice-to-have. As always, failure is communicated via onerror.
