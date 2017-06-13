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

This document proposes an API to create custom animations that execute inside an isolated execution
environment, *worklet*. It aims to be compatible with Web Animations and uses existing constructs as
much as possible. We believe this API hits a sweet spot in balancing among performance, richness,
and rationality for addressing our key use cases.

This design supersedes our [CompositorWorker proposal][cw-proposal].

# Motivating Use Cases

* Scroll-linked effects:
  -   Parallax ([demo](https://googlechrome.github.io/houdini-samples/animation-worklet/parallax-scrolling/))
  -   Animated scroll headers, eg. "hidey-bars" ([demo](https://googlechrome.github.io/houdini-samples/animation-worklet/twitter-header/), [twitter](https://twitter.com/LEGO_Group), [Polymer `paper-scroll-header-panel`](https://elements.polymer-project.org/elements/paper-scroll-header-panel?view=demo:demo/index.html))
  -  Springy sticky elements ([demo](http://googlechrome.github.io/houdini-samples/animation-worklet/spring-sticky/))

* Animations with custom timing functions (particularly those that are not calculable a priori)

  -   Spring timing function ([demo](https://googlechrome.github.io/houdini-samples/animation-worklet/spring-timing/))

* Location tracking and positioning:

  -   Position: sticky

* Procedural animation of multiple elements in sync:

  -   Efficient Expando ([demo](http://googlechrome.github.io/houdini-samples/animation-worklet/expando/), [more info](https://developers.google.com/web/updates/2017/03/performant-expand-and-collapse))
  -   Compositing growing / shrinking box with border (using 9 patch)

* Animating scroll offsets:

  -   Having multiple scrollers scroll in sync e.g. diff viewer keeping old/new in sync when you
      scroll either ([demo](https://googlechrome.github.io/houdini-samples/animation-worklet/sync-scroller/))
  -   Implementing smooth scroll animations (e.g., custom physic based fling curves)

***Note***:  Demos work best in the latest Chrome Canary with the experimental
web platform features enabled (`--enable-experimental-web-platform-features`
flag) otherwise they fallback to using main thread rAF to emulate the behaviour.



# WIP Design
We are actively working on a [newer version](WIP.md) to make the programming model much
closer to Web Animations model.

# Specification
The [draft specification](https://wicg.github.io/animation-worklet) is *out dated* we are actively working on updating
the draft following agreements on Houdini Tokyo F2F meeting on the new direction of WIP design.




[roc-thread]: https://lists.w3.org/Archives/Public/public-houdini/2015Mar/0020.html
[cw-proposal]: https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md
