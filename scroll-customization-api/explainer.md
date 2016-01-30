# Scroll customization explained

Many native mobile applications have [UI effects that interact with scrolling](https://github.com/w3c/css-houdini-drafts/blob/master/scroll-customization-api/UseCases.md), for example snapping the scroll position to image boundaries in an image carousell.  To do this web developers must [resort](http://cubiq.org/iscroll-5) to re-implementing all of scrolling on top of raw input events. There are four major drawbacks with such an approach:
- Threaded scrolling is disabled, so any main thread work >16ms will lead to dropped frames.
- Accessibility is often broken, as the browser (and any assistive technologies) have no idea that scrolling is occurring.
- Such components cannot compose properly with other scrollers (native or JS), for example for proper scroll chaining.
- It is very difficult or impossible to re-implement browser scrolling behavior exactly (on every platform), so such scrolling ends up not feeling/looking right to the user (eg. fling physics).

The fundamental problem here is that scrolling on the web is a big "magical" black-box.  In other UI frameworks scrolling is usually implemented as a library (with extensibility points) on top of primitives.  The goal of the Houdini Scroll Customization proposal is to break open this black box to make scrolling on the web [extensible](https://extensiblewebmanifesto.org/).

## Threaded scrolling

Modern browsers implement scrolling off of the main JavaScript thread to ensure that scrolling can be serviced reliably at 60fps.  This proposal builds on [Compositor Worker](https://github.com/ianvollick/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md) to permit customizations that typically run in-sync with scrolling.  In the future we may also want high performance applications to be able to opt-out of threaded scrolling and also use a variant of these APIs from the main JavaScript execution context.

## ScrollIntent - a primitive abstraction

In order to explain scrolling, we need to introduce an abstraction that sits above raw input (eg. `wheel` and `touchmove` events) but below the effect that scrolling has (changing `scrollTop` and generation of `scroll` events).  `ScrollIntent` represents the user's desire to scroll by a specific number of pixels (as well as additional details about the scroll).  

TODO: Picture showing touch/wheel/keyboard input -> scroll intent -> tagetting logic -> Element::applyScrollIntent -> set scrollTop

## Examples

TODO
