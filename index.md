---
title: Animation Worklet Explainer
---

# Animation Worklet Explainer
---
# Overview

git remotegit AnimationWorklet is a new primitive for creating scroll-linked and other high performance
procedural animations on the web.

{:toc}

# Introduction

Scripted effects (written in response to `requestAnimationFrame` or async `onscroll` events) are
rich but are subject to main thread jankiness. On the other hand, accelerated CSS transitions and
animations can be fast (for a subset of *accelerated* properties) but are not rich enough to enable
[many common use cases](#motivating-use-cases) and currently have no way to access scroll offset
and other user input. This is why scripted effects are still very popular for implementing common
effects such as hidey-bars, parallax, position:sticky, and etc. We believe (and others [agree][roc-
thread] that there is a need for a new primitive for creating fast and rich visual effects with the
ability to respond to user input (e.g., scroll).

This document proposes an API to animate a small subset of accelerated properties inside an
isolated execution environment, *worklet*. We believe this API hits a sweet spot, one that is
currently missing in the platform, in balancing among performance, richness, and rationality for
addressing our key use cases. In particular by limiting ourselves to a subset of accelerated
properties we give up some richness to gain performance while maintaining rationality. Finally, it
is possible to fine tune this trade-off in future iteration of this API by exposing additional
options and without fundamentally reworking this design.

# Motivating Use Cases

* Scroll-linked effects:
  -   Parallax
  -   Hidey-bar

* Animations with custom timing functions (particularly those that are not calculable a priori)

  -   Spring timing function

* Location tracking and positioning:

  -   Position: sticky

* Procedural animation of multiple elements in sync:

  -   Compositing growing / shrinking box with border (using 9 patch)

* Animating scroll offsets:

  -   Having multiple scrollers scroll in sync (e.g. diff viewer keeping old/new in sync when you
      scroll either)
  -   Implementing smooth scroll animations (e.g., custom physic based fling curves)

* Custom effect libraries with reliable performance.

# Examples

Below is a set of simple examples to showcase the syntax and API usage.

## Example 1. A fade-in animation with spring timing


Define animator in the worklet scope:

```javascript
registerAnimator('spring-fadein', class SpringAnimator {
  static inputProperties =  ['--spring-k'];
  static outputProperties =  ['opacity'];
  static inputTime = true;

  animate(root, children, timeline) {
    children.forEach(elem => {
      // read a custom css property.
      const k = elem.styleMap.get('--spring-k') || 1;
      // compute progress using a fancy spring timing function.
      const effectiveValue = springTiming(timeline.currentTime, k);
      // update opacity accordingly.
      elem.styleMap.opacity = effectiveValue;
    });
  }

  springTiming(timestamp, k) {
    // calculate fancy spring timing curve and return a sample.
    return 0.42;
  }

});
```

Assign elements to the animator declaratively in CSS:

```html
.myFadin {
  animator:'spring-fadein';
}

<section class='myFadein'></section>
<section class='myFadein' style="--spring-k: 25;"></section></pre>

```

## Example 2. Multiple Parallax animations


Register the animator in AnimationWorklet scope:

```javascript
registerAnimator('parallax', class ParallaxAnimator {
  static inputProperties = ['transform', '--parallax-rate'];
  static outputProperties = ['transform'];
  static rootInputScroll = true;

  animate(root, children) {
    // read scroller's vertical scroll offset.
    const scrollTop = root.scrollOffsets.top;
    children.forEach(background => {
        // read parallax rate.
        const rate = background.styleMap.get('--parallax-rate');
        // update parallax transform.
        let t = background.styleMap.transform;
        t.m42 =  rate * scrollTop;
        background.styleMap.transform = t;
      });
    });
  }
});
```

Declare and assign elements to animations:

```html
<style>
.parallax_scroller  {
  animator-root: parallax;
  overflow: scroll;
}

.parallax_scroller > .bg {
  animator: parallax;
  position: absolute;
  opacity: 0.5;
}
</style>

<div class='parallax_scroller'>
  <div class='bg' style='--parallax-rate: 0.2'></div>
  <div class='bg' style='--parallax-rate: 0.5'></div>
</div>

<div class='parallax_scroller'>
  <div class='bg'></div>
</div>
```

Define custom CSS properties in Document Scope:


```javascript
CSS.registerProperty({
  name: '--parallax-rate',
  inherits: false,
  initial: 0.2,
  syntax: '<number>'
});

```

## Example 3. Position Sticky


Register the animator in AnimationWorklet scope:


```javascript
// worklet scope

registerAnimator('top-sticky', class TopStickyAnimator {
  static inputProperties = ['--trigger-point'];
  static outputProperties = ['transform'];
  static rootInputScroll = true;

  animate(root, children) {
    // read scroller's vertical scroll offset.
    const scrollTop = root.scrollOffsets.top;

   children.forEach(sticky => {
        const triggerPoint = child.styleMap.get('--trigger-point');
        // if we have scrolled passed the trigger point the sticky element needs
        // to behave as if fixed. We do this by using a transform to position
        // the element relative to its container.
        const stickyOffset = Math.max(0 , scrollTop - triggerPoint);
        sticky.styleMap.transform = new CSSTransformMatrix({m42: stickyOffset});
      });
    });
  }
});
```

In Document scope:

```html

<style>
.sticky_container {
  animator-root: top-sticky;
  overflow: scroll;

}
.sticky {
  animator: top-sticky;
}

</style>

<div class="sticky_container">
   <!-- Next element is both an sticky root and and an sticky children. :) -->
   <div class="sticky_container sticky">
      <div class="sticky"></div>
    </div>
</div>

<script>
onload = (e) => {
  document.querySelectorAll('.sticky').forEach(stickyEl => {

  const scrollerEl = findAncestorScroller(stickyEl);
  // calculate scroll trigger point based on stickyEl BCR and scrollerEl BCR and scrollHeight
  const triggerPoint = calculateLimits(stickyEl, scrollerEl); // e.g., 100

  stickyEl.style = '--trigger-point: ' + triggerPoint + 'px';
}

</script>
```

# Key Concepts

## Animator Root & Child Elements

Each animator instance is associated with a single root element and optionally many child elements.
Animator child elements will come from the root element’s DOM sub-tree. These two category of
elements have their own defined inputs and outputs.

Two CSS properties (`animator` and `animator-root`) may be used to assign an HTML elements to an
animator instance either as a root or a child.

The ability to operate (read/write attributes) on many elements in a single callback enables
powerful effects that are very hard to achieve if an animator was to operate on a single element.

### Root Element

The document’s root element is the default root element for each registered animator. Additional
HTML elements may be designated as root element for a given animator using `animator-root:
animator-identifier` CSS syntax. A new animator instance is constructed for each root element and
its lifetime is tied to the element’s lifetime. The root element and all the child elements in its
DOM sub-tree associated with this animator name get assigned to this animator instance. See below
for more details.

### Child Elements

Any HTML element may be assigned to an animator instance using `animator: animator-identifier` CSS
syntax. In this case, the element is assigned as a child element to the first ancestor animator of
the given name.

***Note:*** The animator receives this in a flat list but we can also consider sending a sparse
tree instead.

## Assigning an Element to an Animator Instance

As discussed, an animator gets assigned a single root element and optionally many children
elements. Assigning an element to an animator instance involves the following:


1.  The element would be treated as if it has an `will-change` attribute for each of its output
    attributes.
2.  An `AnimationProxy` is constructed for the element allowing read and write to declared input
    and output properties.
    1.  For any input property defined for this element, the animation proxy’s style map is
        populated with its computed value.
    2.  Similarly the animation proxy’s scroll offset is populated by the element’s scroll offset.
3.  The constructed proxy is passed to the animator instance in the worklet scope and becomes
    available to the animate callback in its next call.
4.  Once `animate` is invoked, the new output values in style map (and similarly output scroll
    offsets) are used to update the corresponding effective values and visuals. Eventually these
    values will be synced backed to the main thread.

## Explicit Input and Output Attributes

All input and output of the animation are declared explicitly. This allows implementations to do
optimizations such as not calling the *animate *callback if no input has changed or if no outputs
have any visible effect. The following inputs and outputs may be declared on the animator class
using static attributes:

**Input**

*   Regular and Custom CSS Properties - `inputProperties` and `rootInputProperties` (list of
    identifiers)
*   Scroll Offset - `inputScroll` and `rootInputScroll` (boolean)
*   Time - `inputTime  (boolean)

**Output**


*   [“Fast” CSS Properties](#limiting-mutations-to-fast-subset) - `outputProperties` and
    `rootOutputProperties` (list of identifiers)
*   Scroll Offset - `outputProperties` and `rootOutputProperties` (boolean)

## Falling Out of Sync

The API is designed to allow animation worklets to run on threads other than the main thread. In
particular, it is recommended to run them in a dedicated thread and provide a best-effort attempt
to run in sync with frame production in compositor. This ensures the animations will not be
impacted by jank on main thread. It is still possible for such animation to slip in relation with
frame production if *animate* callback takes a long time. We believe such slippage is going to be a
rare event because there is no other tasks beside authored animation tasks running on the thread
and also the exposed features are limited to the fast subset (see below).

## Limiting Mutations to Fast Subset

We initially plan to limit the mutable attributes to a  "fast" subset which can be mutated on the
fast path of almost all modern browsers.

Proposed Mutable Attributes:

*   Scroll Offsets
*   Transform
*   Opacity

This is necessary to ensure animations can run on the the fast path. In future we may consider
supporting all animatable properties which means running the worklet on main thread. The animator
definition surfaces enough information that makes it possible to decide the target executing thread
in advance.

## Relationship to Web-Animation/CSS Transition

Effective values from animator gets synced back to the main thread. These values sit at the top of
the animation [effect stack][effect-stack] meaning that they overrides all values from other
animations (except CSS transitions). The value is to be treated as a forward-filling animation with
a single key-frame i.e., the effective value remains in effect until there is a new value from
animator.

# CSS Syntax


```
animator: [ <animator-id> ]#
animator-root: [ <animator-id> ]#

where <animator-id> is a <custom-ident>
```

# Web IDL


```webidl
partial interface Window {
    [SameObject] readonly attribute Worklet animationWorklet;
};
```

```webidl
callback VoidFunction = void (); // a JS class

[Global=(Worklet,AnimationWorklet),Exposed=AnimationWorklet]
interface AnimationWorkletGlobalScope : WorkletGlobalScope {
    void registerAnimator(DOMString name, VoidFunction animatorCtor);
};
```



```webidl
// animationCtor should be a class with the following structure
callback interface AnimatorCtor {
    static boolean inputTime = false;
    static inputProperties = [];
    static outputProperties = [];
    static rootInputProperties = [];
    static rootOutputProperties = [];
    void animate(AnimationProxy root, sequence<AnimationProxy> children, optional AnimationTimeline timeline);
};
```


```webidl
dictionary ScrollOffests {
    unrestricted double left;
    unrestricted double top;
};

[
    Exposed=(Window,AnimationWorklet),
] interface AnimationProxy {
    attribute ScrollOffests scrollOffsets;
    attribute StylePropertyMap styleMap;
};
```

# Contributors

This design supersedes our [CompositorWorker proposal][cw-proposal] and was possible by key contribution from:

*   Rob Flack (flackr@)
*   Ian Vollick (vollick@)
*   Ian Kilpatrick (ikilpatrick@)
*   Sadrul Chowdhury (sadrul@)
*   Shane Stephens (shanes@)

And many other members of Chrome web platform team.


[roc-thread]: https://lists.w3.org/Archives/Public/public-houdini/2015Mar/0020.html
[cw-proposal]: https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md
[effect-stack]: https://w3c.github.io/web-animations/#combining-effects