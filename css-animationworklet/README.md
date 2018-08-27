# Animation Worklet Explainer
---

# Overview

AnimationWorklet is a new primitive for creating scroll-linked and other high performance
procedural animations on the web.  It is being incubated here as part of the
[CSS Houdini task force](https://github.com/w3c/css-houdini-drafts/wiki), and if successful will be
transferred to that task force for full standardization.

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
  -   Parallax ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/parallax-scrolling/))
  -   Animated scroll headers, eg. "hidey-bars" ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/twitter-header/), [twitter](https://twitter.com/LEGO_Group), [Polymer `paper-scroll-header-panel`](https://elements.polymer-project.org/elements/paper-scroll-header-panel?view=demo:demo/index.html))
  -  Springy sticky elements ([demo](http://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-sticky/))

* Animations with custom timing functions (particularly those that are not calculable a priori)

  -   Spring timing function ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-timing/))

* Location tracking and positioning:

  -   Position: sticky

* Procedural animation of multiple elements in sync:

  -   Efficient Expando ([demo](http://googlechromelabs.github.io/houdini-samples/animation-worklet/expando/), [more info](https://developers.google.com/web/updates/2017/03/performant-expand-and-collapse))
  -   Compositing growing / shrinking box with border (using 9 patch)

* Animating scroll offsets:

  -   Having multiple scrollers scroll in sync e.g. diff viewer keeping old/new in sync when you
      scroll either ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/sync-scroller/))
  -   Implementing smooth scroll animations (e.g., custom physic based fling curves)

***Note***:  Demos work best in the latest Chrome Canary with the experimental
web platform features enabled (`--enable-experimental-web-platform-features`
flag) otherwise they fallback to using main thread rAF to emulate the behaviour.


# Key Concepts

## Animation Worklet Global Scope
A [worklet global scope](https://drafts.css-houdini.org/worklets/#the-global-scope) that is created
by Animation Worklet. Note that Animation Worklet creates multiple such scopes and uses them to
execute user defined effects.

## WorkletAnimation
`WorkletAnimation` is a subclass of Animation that can be used to create an custom animation effect
that runs inside a standalone animation worklet scope. A worklet animation has a corresponding
animator instance in a animation worklet scope which is responsible to drive its keyframe effects.
Here are the key differences compared to a regular web animation:
  - AnimationId should match a specific animator class registered in the animation worklet scope.
  - `WorkletAnimation` may have multiple timelines (including `ScrollTimeline`s).
  - `WorkletAnimation` may have a custom properties bag that can be cloned and provided to animator
    constructor when it is being instantiated.

Note that worklet animations expose same API surface as other web animations and thus they may be
created, played, paused, inspected, and generally controlled from main document scope. Here is how
various methods roughly translate:

  - cancel(): cancels the animation and the corresponding animator instance is removed.
  - play(): starts the animation and the corresponding animator instance may get its `animate` function
    called periodically as a result of changes in its timelines.
  - pause(): pauses the animation and the corresponding animator instance no longer receives
    `animate` calls.
  - finish(): invokes `finish` on the corresponding animator instance.
  - reverse() or mutating playbackRate: invokes `playbackRateChanged` on the corresponding
     animator instance.

## ScrollTimeline
[ScrollTimeline](https://wicg.github.io/scroll-animations/#scrolltimeline) is a concept introduced in
scroll-linked animation proposal. It defines an animation timeline whose time value depends on
scroll position of a scroll container. `ScrollTimeline` can be used an an input timeline for
worklet animations and it is the intended mechanisms to give read access to scroll position.

## GroupEffect
[GroupEffect](https://w3c.github.io/web-animations/level-2/#the-animationgroup-interfaces) is a
concept introduced in Web Animation Level 2 specification. It provides a way to group multiple
effects in a tree structure. `GroupEffect` can be used as the output for worklet animations. It
makes it possible for worklet animation to drive effects spanning multiple elements.

**TODO**: At the moment, `GroupEffect` only supports just two different scheduling models (i.e.,
parallel, sequence). These models governs how the group effect time is translated to its children
effect times by modifying the child effect start time. AnimationWorklet allows a much more flexible
scheduling model by making it possible to to set children effect's local time directly. In other
words we allow arbitrary start time for child effects. This is something that needs to be added to
level 2 spec.

## Multiple Timelines
Unlike typical animations, worklet animations can be attached to multiple timelines. This is
necessary to implement key usecases where the effect needs to smoothly animate across different
timelines (e.g., scroll and wall clock).

### Primary Timeline
The first timeline is considered the *primary timeline*. The only purpose of the primary timeline is
to make integration with existing web animation machinery easier, in particular the primary timeline
time will be used anywhere the web animation API needs to expose a time value, for example in
[event timeline time](https://w3c.github.io/web-animations/level-2/#event-timeline-time), or
[event current time](https://w3c.github.io/web-animations/level-2/#event-current-time).


**TODO**: We are considering API designs that can make it possible for an animation to observe multiple
timelines but only gets activated on a (dynamic) subset of them. This ensures we can be more
efficient when updating the animation.

## Animator Migration
The animators are not guaranteed to run in the same global scope (or underlying thread) for their
lifetime duration. For example, a user agents is free to initially run the animator on main thread
but later decide to migrate it off main thread to get certain performance optimizations. To allow
worklet animators to keep their state across migrations, the API provides the following lifetime
hooks:

```js
// in document scope
new WorkletAnimation('animation-with-local-state', [], [], {value: 1});
```


```js
registerAnimator('animation-with-local-state', class {
  constructor(options, state) {
    // |options| may be either:
    //  - The user provided options bag passed into the WorkletAnimation constructor on first initialization i.e, {value: 1}.
    //  - The object returned by |destroy| after each migration i.e. {value: 42}.
    this.options_ = options;
    this.state_ = state || {value: Math.random()};
  }

  animate(timelines, effect) {
    this.state_.value += 0.1;
    effect.localTime = this.state_.value;
  }

  destroy() {
    // Invoked before each migration attempts.
    // The returned object must be structure clonable and will be passed to constructor to help
    // animator restore its state after migration to the new scope.
    return this.state_;
  }
});
```

# Examples

**TODO**: Add gifs that visualize these effects

## Hidey Bar
An example of header effect where a header is moved with scroll and as soon as finger is lifted
it animates fully to close or open position depending on its current position.


``` html
<div id='scrollingContainer'>
  <div id='header'>Some header</div>
  <div>content</div>
</div>

<script>
await CSS.animationWorklet.addModule('hidey-bar-animator.js');
const scrollTimeline = new ScrollTimeline($scrollingContainer, {timeRange: 100});
const documentTimeline = document.timeline;


const animation = new WorkletAnimation('hidey-bar',
  new KeyframeEffect($header,
                      [{transform: 'translateX(100px)'}, {transform: 'translateX(0px)'}],
                      {duration: 100, iterations: 1, fill: 'both' })
  scrollTimeline,
  {scrollTimeline, documentTimeline},
);
animation.play();
</script>
```

hidey-bar-animator.js:
```js
registerAnimator('hidey-bar', class {

  constructor(options) {
    this.scrollTimeline_ = options.scrollTimeline;
    this.documentTimeline_ = options.documentTimeline;
  }

  animate(currentTime, effect) {
    const scroll = this.scrollTimeline_.currentTime;  // [0, 100]
    const time = this.documentTimeline_.currentTime;

    // **TODO**: use a hypothetical 'phase' property on timeline as a way to detect when user is no
    // longer actively scrolling. This is a reasonable thing to have on scroll timeline but we can
    // fallback to using a timeout based approach as well.
    const activelyScrolling = this.scrollTimeline_.phase == 'active';

    let localTime;
    if (activelyScrolling) {
      this.startTime_ = undefined;
      localTime = scroll;
    } else {
      this.startTime_ = this.startTime_ || time;
      // Decide on close/open direction depending on how far we have scrolled the header
      // This can even do more sophisticated animation curve by computing the scroll velocity and
      // using it.
      this.direction_ = scroll >= 50 ? +1 : -1;
      localTime = this.direction_ * (time - this.startTime_);
    }

    // Drive the output effects by setting its local time.
    effect.localTime = localTime;
});

```


## Twitter Header
An example of twitter profile header effect where two elements (avatar, and header) are updated in
sync with scroll offset.

```html

<div id='scrollingContainer'>
  <div id='header' style='height: 150px'></div>
  <div id='avatar'><img></div>
</div>

<script>
await CSS.animationWorklet.addModule('twitter-header-animator.js');
const animation = new WorkletAnimation('twitter-header',
  [new KeyframeEffect($avatar,  /* scales down as we scroll up */
                      [{transform: 'scale(1)'}, {transform: 'scale(0.5)'}],
                      {duration: 1000, iterations: 1}),
    new KeyframeEffect($header, /* loses transparency as we scroll up */
                      [{opacity: 0}, {opacity: 0.8}],
                      {duration: 1000, iterations: 1})] ,
    new ScrollTimeline($scrollingContainer, {timeRange: 1000, startScrollOffset: 0, endScrollOffset: $header.clientHeight}),
);
animation.play();
</script>
```

twitter-header-animator.js:
```js
registerAnimator('twitter-header', class {
  constructor(options) {
    this.timing_ = new CubicBezier('ease-out');
  }

  clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  animate(currentTime, effect) {
    const scroll = currentTime;  // [0, 1]

    // Drive the output group effect by setting its children local times.
    effect.children[0].localTime = scroll;
    // Can control the child effects individually
    effect.children[1].localTime = this.timing_(this.clamp(scroll, 0, 1));
  }
});

```

### Parallax
```html
<style>
.parallax {
    position: fixed;
    top: 0;
    left: 0;
    opacity: 0.5;
}
</style>
<div id='scrollingContainer'>
  <div id="slow" class="parallax"></div>
  <div id="fast" class="parallax"></div>
</div>

<script>
await CSS.animationWorklet.addModule('parallax-animator.js');
const scrollTimeline = new ScrollTimeline($scrollingContainer, {timeRange: 1000});
const scrollRange = $scrollingContainer.scrollHeight - $scrollingContainer.clientHeight;

const slowParallax = new WorkletAnimation(
    'parallax',
    new KeyframeEffect($parallax_slow, [{'transform': 'translateY(0)'}, {'transform': 'translateY(' + -scrollRange + 'px)'}], scrollRange),
    scrollTimeline,
    {rate : 0.4}
);
slowParallax.play();

const fastParallax = new WorkletAnimation(
    'parallax',
    new KeyframeEffect($parallax_fast, [{'transform': 'translateY(0)'}, {'transform': 'translateY(' + -scrollRange + 'px)'}], scrollRange),
    scrollTimeline,
    {rate : 0.8}
);
fastParallax.play();
</script>

```

parallax-animator.js:

```js
// Inside AnimationWorkletGlobalScope.
registerAnimator('parallax', class {
  constructor(options) {
    this.rate_ = options.rate;
  }

  animate(currentTime, effect) {
    effect.localTime = currentTime * this.rate_;
  }
});
```


# WEBIDL

`WorkletAnimation` extends `Animation` and adds a getter for its timelines.
Its constructor takes:
 -  `animatiorId` which should match the id of an animator which is registered in
the animation worklet scope.
 - A sequence of effects which are passed into a `GroupEffect` constructor.
 - A sequence of timelines, the first one of which is considered primary timeline and passed to
   `Animation` constructor.

```webidl

[Constructor (DOMString animatorName,
              optional (AnimationEffectReadOnly or array<AnimationEffectReadOnly>)? effects = null,
              AnimationTimeline? timeline,
              optional WorkletAnimationOptions)]
interface WorkletAnimation : Animation {
        readonly attribute DOMString animatorName;
}
```

**TODO**: At the moment `GroupEffect` constructor requires a timing but this seems unnecessary for
`WorkletAnimation` where it should be possible to directly control individual child effect local
times. We need to bring this up with web-animation spec.

`AnimationEffectReadOnly` gets a writable `localTime` attribute which may be used to drive the
effect from the worklet global scope.

```webidl
partial interface AnimationEffectReadOnly {
    [Exposed=Worklet]
    // Intended for use inside Animation Worklet scope to drive the effect.
    attribute double localTime;
};

```




# Specification
The [draft specification](https://https://drafts.css-houdini.org/css-animationworklet) is
the most recent version.


[roc-thread]: https://lists.w3.org/Archives/Public/public-houdini/2015Mar/0020.html
[cw-proposal]: https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md
