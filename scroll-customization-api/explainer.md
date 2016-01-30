# Scroll customization

Many native mobile applications have [UI effects that interact with scrolling](https://github.com/w3c/css-houdini-drafts/blob/master/scroll-customization-api/UseCases.md), for example snapping the scroll position to image boundaries in an image carousell.  To do this web developers must [resort](http://cubiq.org/iscroll-5) to re-implementing all of scrolling on top of raw input events. There are four major drawbacks with such an approach:
- Threaded scrolling is disabled, so any main thread work >16ms will lead to dropped frames.
- Accessibility is often broken, as the browser (and any assistive technologies) have no idea that scrolling is occurring.
- Such components cannot compose properly with other scrollers (native or JS), for example for proper scroll chaining.
- It is very difficult or impossible to re-implement browser scrolling behavior exactly (on every platform), so such scrolling ends up not feeling/looking right to the user (eg. fling physics).

The fundamental problem here is that scrolling on the web is a big "magical" black-box.  In other UI frameworks scrolling is usually implemented as a library (with extensibility points) on top of primitives.  The goal of the Houdini Scroll Customization proposal is to break open this black box to make scrolling on the web [extensible](https://extensiblewebmanifesto.org/).

## Supporting Threaded scrolling

Modern browsers implement scrolling off of the main JavaScript thread to ensure that scrolling can be serviced reliably at 60fps.  We want to allow arbitrary scroll effects to be written using JavaScript that runs every scroll frame. This proposal builds on [Compositor Worker](https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md) to permit customizations that typically run in-sync with scrolling.

In the future we also want high performance applications to be able to opt-out of threaded scrolling and use a variant of these APIs from the main JavaScript execution context.  The details of how to permit such customization without risking poor performance are complex and controversial and so are not yet covered as part of this proposal.  But regardless of the thread in which it's executing, the mental model for scroll customization is the same.

## ScrollIntent

In order to explain scrolling, we need to introduce an abstraction that sits above raw input (eg. `wheel` and `touchmove` events) but below the effect that scrolling has (changing `scrollTop` and generation of `scroll` events).  `ScrollIntent` represents the user's desire to scroll by a specific number of pixels (as well as additional details about the scroll such has the phase and velocity).  A `Element` has a new method called `applyScroll` which takes a `ScrollIntent` and applies it, which by default just means updating `scrollTop` and `scrollLeft`.

![ScrollIntent](ScrollIntent.png?raw=true)

## Customizing `applyScroll`

The default `applyScroll` behavior can be overridden to do something competely different whenever the user attempts to scroll the element.  For example, to support rotating a 3d carousell using all the native scroll physics and composition, you might use code like this (hypothetical syntax):

Main Thread
```JavaScript
var carousel_proxy = new CompositorProxy(carousel, [transform]);
var worker = new CompositorWorker('carousel.js');
worker.postMessage(carousel_proxy);
```

On the CompositorWorker
```JavaScript
onmessage = function(e) {
  var carousel = e.data;
  carousel.applyScroll = function(scrollIntent) {
      this.transform.rotateX += scrollIntent.deltaX;
      scrollIntent.consumeDelta(scrollIntent.deltaX, 0);
  };
};
```

## More examples

TODO
