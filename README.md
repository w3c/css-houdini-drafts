# Animation Worklet Explainer
---

# Overview

AnimationWorklet is a new primitive for creating scroll-linked and other high performance
procedural animations on the web.  It is being incubated here as part of the [CSS Houdini task force](https://github.com/w3c/css-houdini-drafts/wiki), and if successful will be transferred to that task force for full standardization.

# Introduction

Scripted effects (written in response to `requestAnimationFrame` or async `onscroll` events) are
rich but are subject to main thread jankiness. On the other hand, accelerated CSS transitions and
animations can be fast (for a subset of *accelerated* properties) but are not rich enough to enable
[many common use cases](#motivating-use-cases) and currently have no way to access scroll offset
and other user input. This is why scripted effects are still very popular for implementing common
effects such as hidey-bars, parallax, position:sticky, and etc. We believe (and others
[agree][roc-thread]) that there is a need for a new primitive for creating fast and rich visual
effects with the ability to respond to user input such as scroll.

This document proposes an API to animate a small subset of accelerated properties inside an
isolated execution environment, *worklet*. We believe this API hits a sweet spot, one that is
currently missing in the platform, in balancing among performance, richness, and rationality for
addressing our key use cases. In particular by limiting ourselves to a subset of accelerated
properties we give up some richness to gain performance while maintaining rationality. Finally, it
is possible to fine tune this trade-off in future iteration of this API by exposing additional
options and without fundamentally reworking this design.

This design supersedes our [CompositorWorker proposal][cw-proposal].

# Motivating Use Cases

* Scroll-linked effects:
  -   Parallax ([demo](https://flackr.github.io/houdini-samples/animation-worklet/parallax-scrolling/))
  -   Animated scroll headers, eg. "hidey-bars" ([demo](https://flackr.github.io/houdini-samples/animation-worklet/twitter-header/), [twitter](https://twitter.com/LEGO_Group), [Polymer `paper-scroll-header-panel`](https://elements.polymer-project.org/elements/paper-scroll-header-panel?view=demo:demo/index.html))

* Animations with custom timing functions (particularly those that are not calculable a priori)

  -   Spring timing function ([demo](https://flackr.github.io/houdini-samples/animation-worklet/spring-timing/))

* Location tracking and positioning:

  -   Position: sticky
  
* Procedural animation of multiple elements in sync:

  -   Compositing growing / shrinking box with border (using 9 patch)

* Animating scroll offsets:

  -   Having multiple scrollers scroll in sync e.g. diff viewer keeping old/new in sync when you
      scroll either ([demo](https://flackr.github.io/houdini-samples/animation-worklet/sync-scroller/))
  -   Implementing smooth scroll animations (e.g., custom physic based fling curves)

***Note***:  Demos work best in the latest Chrome Canary with the experimental
web platform features enabled (`--enable-experimental-web-platform-features`
flag) otherwise they fallback to using main thread rAF to emulate the behaviour.

# Specification

We know have an initial [draft specification](https://wicg.github.io/animation-worklet).
In particular you can se the CSS Notation, Web IDL, and [examples](https://wicg.github.io/animation-worklet/#examples).

# Key Concepts

## Animator Root & Child Elements

Each animator instance is associated with a single root element and optionally many child elements.
Animator child elements will come from the root element’s DOM sub-tree. These two category of
elements have their own defined inputs and outputs.

Two CSS properties (`animator` and `animator-root`) may be used to assign an HTML elements to an
animator instance either as a root or a child.

The ability to operate (read/write attributes) on many elements in a single callback enables
powerful effects that are difficult to achieve if an animator was to operate on a single element.

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
have any visible effect.

## Scroll Input as a Timeline
Each animator may declare an scroll timeline as an input. The animator root element (or its nearest scroller ancestor) will be the source for this scroll timeline.

## Falling Out of Sync

The API is designed to allow animation worklets to run on threads other than the main thread. In
particular, it is recommended to run them in a dedicated thread and provide a best-effort attempt
to run in sync with visual frame production. This ensures the animations will not be impacted by jank on
main thread. It is still possible for such animation to slip in relation with frame production if
*animate* callback cannot be completed in time. We believe such slippage is going to be rare in 
particular if animators are running on their dedicated thread and the effect avoid layout inducing
attributes.


## Relationship to Web-Animation/CSS Transition

Effective values from animator gets synced back to the main thread. These values sit at the top of
the animation [effect stack][effect-stack] meaning that they overrides all values from other
animations. The value is to be treated as a forward-filling animation with a single key-frame 
i.e., the effective value remains in effect until there is a new value from animator.



[roc-thread]: https://lists.w3.org/Archives/Public/public-houdini/2015Mar/0020.html
[cw-proposal]: https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md
[effect-stack]: https://w3c.github.io/web-animations/#combining-effects
