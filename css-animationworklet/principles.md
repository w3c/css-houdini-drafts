# Animation Worklet Design Principles and Goals
***for rich interactive effects on the Web Platform***


## Problem and Motivation

**Fact**: Fact: It is difficult to build smooth rich interactive effects on the web.

**Why do we care?**
Silky smooth rich interactive user interfaces are now a [basic user expectation][performance] on
modern computing platforms. For web platform to remain competitive it should be capable of high
fidelity, smooth, responsive UI.


**Where is the difficulty?**
Three key aspects of rich interactive effects are: smoothness, responsiveness to input (a.k.a. R & A
of [RAILS model][rails]) and their rich interaction model.

The two main methods for creating animations on the web fall short in at least one of these aspects:

- CSS (Web) Animations: Aimed at supporting stateless declarative time-driven effects. The
  expressiveness is sufficient for common time-based effects. The resulting animation can be smooth
  <sup>[1](#footnote1)</sup>. However it's unclear how this model can be scaled to handle the
  multi-dimensional inputs, conditional values, and statefulness required by the use cases below.
- requestAnimationFrame: Aimed at creating scripted animation effects. It can support rich
  interaction models but it is difficult to make smooth or responsive. This expressiveness of
  Javascript coupled with access to all input methods, application state and dom makes this API
  capable of building rich interactive effects. However these can only run on main thread alongside
  all other scripts<sup>[2](#footnote2)</sup> which severely hampers their responsiveness and
  smoothness. Chrome [studies](https://tdresser.github.io/input-latency-deep-reports/) have shown that script is the main culprit to user responsiveness issues.

Animation Worklet aims to help bridge the gap between these two.

## Animation Worklet Vision

[Animation Worklet][specification] aims to rectify this shortcomings by enabling animations that can
be:

*   rich (imperative, stateful)
*   fast-by-default (isolated from main thread)
*   respond to rich input e.g., touch, gesture, scroll.

Animation Worklet is a primitive in the [extensible web](https://extensiblewebmanifesto.org/) spirit.
It exposes browser's fast path to applications in a way that it was never before and reduces browser
magic.

Examples of rich interactive effects that are (or will be made) possible with Animation Worklet:


*   Scroll driven effects:
    *   [Hidey-bar](https://googlechromelabs.github.io/houdini-samples/animation-worklet/twitter-header/): animation depends on both time and scroll input.
    *   [Parallax](https://googlechromelabs.github.io/houdini-samples/animation-worklet/parallax-scrolling/): Simplest scroll-drive effect.
    *   [Custom paginated slider](http://aw-playground.glitch.me/amp-scroller.html).
    *   Pull-to-refresh: animation depends on both touch and time inputs.
    *   Custom scrollbars.
    *   [More examples](https://github.com/w3c/css-houdini-drafts/blob/master/scroll-customization-api/UseCases.md) of scroll-driven effects.
*   Gesture driven effects:
    *   [Image manipulator](https://github.com/w3c/csswg-drafts/issues/2493#issuecomment-422153926) that scales, rotates etc.
    *   Swipe to dismiss.
    *   Drag-N-Drop.
    *   Tiled panning e.g., Google maps.
*   Stateful script driven effects:
    *   [Spring-based emulations](https://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-timing/).
    *   [Spring-Sticky effect](http://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-sticky/).
    *   Touch-driven physical environments.
    *   [Expando](http://googlechromelabs.github.io/houdini-samples/animation-worklet/expando/): Procedural animations with multiple elements.
*   Animated scroll offsets:
    * Having multiple scrollers scroll in sync e.g. diff viewer keeping old/new in sync when you
      scroll either ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/sync-scroller/))
    * Custom smooth scroll animations (e.g., physic based fling curves)


## First Principle - Richness

Animation Worklet enables developers to create custom animations by providing an `animate` function
that runs inside animation worklet global scope. The animation logic can take advantage of the full
expressive power of JavaScript, maintain local state, modify and coordinated across many elements.
This new extension point in browser animation system enables richer effects that go well beyond what
can be achieved today with Web Animations and closer to what is possible with requestAnimationFrame.

**Further explorations in this direction:** Allow richer access to scrolling machinery (e.g., scroll
customization), custom paint worklets, and outputs beyond existing KeyframeEffect interface.


## Second Principle - Performance

Animation Worklet is designed to be thread agnostic. In particular, it can run off main thread
keeping its performance isolated from main thread (also reducing main thread load).

Animation Worklet API encourages the developers to isolate their critical UI work inside limited
worklet scope with well-specified input and output. This allows user-agent to make much better
scheduling decision about this work and in particular, be much better at maintaining a strict
frame-budget to successfully run these animations on its fast path. Presently the above performance
guarantees are only accessible to a limited set of declarative time-based effects.

**Further explorations in this direction**: Introduce more sophisticated per-animation scheduling
where a slow animation may run at slower frame-rate without affecting other well-behaved animations,
experiment with translating animation code to native code or even GL shaders moving the computation
to GPU for even stronger performance guarantees!


## Third Principle - Interactivity

Animation Worklet is designed to enable support for animations whose input goes beyond just time, a
single-dimensional variable.

Web animation timing model is stateless and driven by a single dimensional variable, time.

Although this model works well for declarative time-based animation, it falls short when it comes to
interactive input-driven effects that are inherently stateful. While it is possible to map simple
forms of input (e.g., [single dimensional scroll](https://wicg.github.io/scroll-animations/#intro))
into time, it is much more difficult (almost impossible) to do so for multi-dimensional stateful
input such as multi-touch and gesture input.

Animation Worklet has the necessary expressive power and richness to easily accommodate the full
richness of multi-dimensional input such as touch, gesture, scroll etc. For example it is trivial to
react to scroll phase change, pointer state change, addition/removal of new pointer or state,
calculate pointer velocity, acceleration and other computed values inside an animation worklet.

**Further explorations in this direction:** Expose pointer and gesture as input to animation
([current proposal](https://github.com/w3c/csswg-drafts/issues/2493#issuecomment-422109535))


# Appendix


## Footnotes

* <a name="footnote1">1</a>: If authors limit themselves to cheap-to-update properties. In Chrome
  these are composited properties e.g., transform, opacity, filter but other engines may have a
  slightly difference subset.


[performance]: https://paul.kinlan.me/what-news-readers-want/
[rails]: https://developers.google.com/web/fundamentals/performance/rail#goals-and-guidelines
[specification]: https://github.com/w3c/css-houdini-drafts/tree/master/css-animationworklet
