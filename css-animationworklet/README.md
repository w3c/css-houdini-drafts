# Animation Worklet Explainer
---

# Overview

Animation Worklet is a new primitive that provides extensibility in web animations and enables high
performance procedural animations on the web. The feature is developed as part of the
[CSS Houdini task force](https://github.com/w3c/css-houdini-drafts/wiki).

The Animation Worklet API provides a method to create scripted animations that control a set of
animation effects. These animations are executed inside an isolated execution environment, *worklet*
which makes it possible for user agents to run such animations  in their own dedicated thread to
provide a degree of performance isolation from main thread. The API is compatible with Web
Animations and uses existing constructs as much as possible.

# Background

Scripted interactive effects (written in response to `requestAnimationFrame`, `pointer events` or
async `onscroll` events) are rich but are subject to main thread jankiness. On the other hand,
accelerated CSS transitions and animations can be fast (for a subset of *accelerated* properties)
but are not rich enough to enable [many common use cases](#motivating-use-cases) and currently have
no way to access key user input (pointer events, gestures, scroll). This is why scripted effects are
still very popular for implementing common effects such as hidey-bars, parallax, pull-to-refresh,
drag-and-drop, swipe to dismiss and etc. Animation Worklet provides is key building block for
enabling creation of smooth rich interactive visual effects on the web while also exposing an
extensibility hook in web animations.


See the [Animation Worklet design principles and goals](principles.md) for a more extended overview
of the motivations behind Animation Worklet and how the design will be evolved to support a growing
set of use cases. Also see [the status document](status.md) for high level implementation status and
timeline. [Here][roc-thread] you may find an earlier high level discussion on general approaches to
address this problem.


# Motivating Use Cases

*   Scroll driven effects:
    *   [Hidey-bar](https://googlechromelabs.github.io/houdini-samples/animation-worklet/twitter-header/): animation depends on both time and scroll input.
    *   [Parallax](https://googlechromelabs.github.io/houdini-samples/animation-worklet/parallax-scrolling/): Simplest scroll-drive effect.
    *   [Custom paginated slider](http://aw-playground.glitch.me/amp-scroller.html).
    *   Pull-to-refresh: animation depends on both touch and time inputs.
    *   Custom scrollbars.
    *   High-fidelity location tracking and positioning
    *   [More examples](https://github.com/w3c/css-houdini-drafts/blob/master/scroll-customization-api/UseCases.md) of scroll-driven effects.
*   Gesture driven effects:
    *   [Image manipulator](https://github.com/w3c/csswg-drafts/issues/2493#issuecomment-422153926) that scales, rotates etc.
    *   Swipe to dismiss.
    *   Drag-N-Drop.
    *   Tiled panning e.g., Google maps.
*   Stateful script driven effects:
    *   [Spring timing emulations](https://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-timing/).
    *   [Spring-Sticky effect](http://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-sticky/).
    *   Touch-driven physical environments.
    *   [Expando](http://googlechromelabs.github.io/houdini-samples/animation-worklet/expando/): Procedural animations with multiple elements.
*   Animated scroll offsets:
    * Having multiple scrollers scroll in sync e.g. diff viewer keeping old/new in sync when you
      scroll either ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/sync-scroller/))
    * Custom smooth scroll animations (e.g., physic based fling curves)
*   Animation Extensibility:
    *  Custom timing functions (particularly those that are not calculable a priori)
    *  Custom animation sequencing which involves complex coordination across multiple effects.


Not all of these usecases are immediately enabled by the current proposed API. However Animation
Worklet provides a powerfull primitive (off main-thread scriped animation) which when combined with
other upcoming features (e.g.,
[Event in Worklets](https://github.com/w3c/css-houdini-drafts/issues/834),
[ScrollTimeline](https://wicg.github.io/scroll-animations/),
[GroupEffect](https://github.com/w3c/csswg-drafts/issues/2071)) can address all these usecases and
allows many of currently main-thread rAF-based animations to move off thread with significant
improvement to their smoothness.
See [Animation Worklet design principles and goals](principles.md) for a more extended discussion
of this.



***Note***:  Demos work best in the latest Chrome Canary with the experimental
web platform features enabled (`--enable-experimental-web-platform-features`
flag) otherwise they fallback to using main thread rAF to emulate the behaviour.


# Key Concepts

## Animation Worklet Global Scope
A [worklet global scope](https://drafts.css-houdini.org/worklets/#the-global-scope) that is created
by Animation Worklet. Note that Animation Worklet creates multiple such scopes and uses them to
execute user defined effects. In particular global scopes are regularly switched to enforce
stateless and stateful animator contracts.


## Animator

Animator is a Javascript class that encapsulates the custom animation logic. Similar to other
Houdinig worklets, animators are registered inside the worklet global scope with a unique name which
can be used to uniquely identify them.


## WorkletAnimation
`WorkletAnimation` is a subclass of Animation that can be used to create an custom animation that
runs inside a standalone animation worklet scope. A worklet animation has a corresponding animator
instance in a animation worklet scope which is responsible to drive its keyframe effects. Here are
the key differences compared to a regular web animation:
  - Name: The name identifies the custom animator class registered in the animation worklet scope.
  - Options: `WorkletAnimation` may have a custom properties bag that is cloned and provided to the
    corresponding animator constructor when it is being instantiated.

Note that worklet animations expose same API surface as other web animations and thus they may be
created, played, paused, inspected, and generally controlled from the main document scope. Here is
how various methods roughly translate:

  - `cancel()`: cancels the animation and the corresponding animator instance is removed.
  - `play()`: starts the animation and the corresponding animator instance gets constructed and
     may get its `animate` function called periodically as a result of changes in its timelines.
  - pause(): pauses the animation and the corresponding animator instance no longer receives
    `animate` calls.
  - finish(), reverse() or mutating playbackRate: these affect the currentTime which is seens by
     the animator instance. (We are considering possiblity of having a `onPlaybackRateChanged`
     callback)

## Statefull and Statelss Animators

Sometimes animation effects require maintaining internal state (e.g., when animation needs to depend
on velocity). Such animators have to explicitly declare their statefulness but by inheritting from
`StatefulAnimator` superclass.

The animators are not guaranteed to run in the same global scope (or underlying thread) for their
lifetime duration. For example user agents are free to initially run the animator on main thread
but later decide to migrate it off main thread to get certain performance optimizations or to tear
down scopes to save resources.

Animation Worklet helps stateful animators to maintain their state across such migration events.
This is done through a state() function which is called and animator exposes its state. Here is
an example:

```js
// in document scope
new WorkletAnimation('animation-with-local-state', keyframes);
```

```js
registerAnimator('animation-with-local-state', class FoorAnimator extends StatefulAnimator {
  constructor(options, state = {velocity: 0, acceleration: 0}) {
    //  state is either undefined (first time) or the state after an animator is migrated across
    // global scope.
    this.velocity = state.velocity;
    this.acceleration = state.acceleration;
  }

  animate(time, effect) {
    if (this.lastTime) {
      this.velocity = time - this.prevTime;
      this.acceleration = this.velocity - this.prevVelocity;
    }
    this.prevTime = time;
    this.prevVelocity = velocity;

    effect.localTime = curve(velocity, acceleration, currentTime);
  }

  state() {
    // Invoked before any migration attempts. The returned object must be structure clonable
    // and will be passed to constructor to help animator restore its state after migration to the
    // new scope.
    return {
      this.velocity,
      this.acceleration
    };
  }

  curve(velocity, accerlation, t) {
     return /* compute some physical movement curve */;
  }
});
```

# Related Concepts

The following concepts are not part of Animation Worklet specification but animation worklet is
designed to take advantage of them to enable a richer set of usecases.

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
effect times by modifying the child effect start time. Animation Worklet allows a much more
flexible scheduling model by making it possible to to set children effect's local time directly. In
other words we allow arbitrary start time for child effects. This is something that needs to be
added to level 2 spec.


# Examples

## Custom Spring Timing

Use Animation Worklet to create animation with a custom spring timing.


```html

<div id='target'></div>

<script>
await CSS.animationWorklet.addModule('spring-animator.js');

const effect = new KeyframeEffect(
  $target,
  {transform: ['translateX(0)', 'translateX(50vw)']},
  {duration: 1000}
);
const animation = new WorkletAnimation('spring', effect, document.timeline, {k: 2, ratio: 0.7});
animation.play();
</script>
```

spring-animator.js:

```js
registerAnimator('spring', class SpringAnimator extends StatelessAnimator {
  constructor(options = {k: 1, ratio: 0.5}) {
    this.timing = createSpring(options.k, options.ratio);
  }

  animate(currentTime, effect) {
    let delta = this.timing(currentTime);
    // scale this by target duration
    delta = delta * (effect.getTimings().duration / 2);
    effect.localTime = delta;
    // TODO: Provide a method for animate to mark animation as finished once
    // spring simulation is complete, e.g., this.finish()
    // See issue https://github.com/w3c/css-houdini-drafts/issues/808
  }
});

function createSpring(springConstant, ratio) {
  // Normalize mass and distance to 1 and assume a reasonable init velocit
  // but these can also become options to this animator.
  const velocity = 0.2;
  const mass = 1;
  const distance = 1;

  // Keep ratio < 1 to ensure it is under-damped.
  ratio = Math.min(ratio, 1 - 1e-5);

  const damping = ratio * 2.0 * Math.sqrt(springConstant);
  const w = Math.sqrt(4.0 * springConstant - damping * damping) / (2.0 * mass);
  const r = -(damping / 2.0);
  const c1 = distance;
  const c2 = (velocity - r * distance) / w;

  // return a value in [0..distance]
  return function springTiming(timeMs) {
    const time = timeMs / 1000; // in seconds
    const result = Math.pow(Math.E, r * time) *
                  (c1 * Math.cos(w * time) + c2 * Math.sin(w * time));
    return distance - result;
  }
}
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
                      {duration: 1000, iterations: 1})],
    new ScrollTimeline({
      scrollSource: $scrollingContainer,
      timeRange: 1000,
      orientation: 'block',
      startScrollOffset: 0,
      endScrollOffset: $header.clientHeight}),
);
animation.play();
</script>
```

twitter-header-animator.js:
```js
registerAnimator('twitter-header', class TwitterHeader extends StatelessAnimator {
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
const scrollTimeline = new ScrollTimeline({
  scrollSource: $scrollingContainer,
  orientation: 'block',
  timeRange: 1000
});
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
registerAnimator('parallax', class Parallax extends StatelessAnimator{
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
The [draft specification](https://drafts.css-houdini.org/css-animationworklet) is
the most recent version.


[roc-thread]: https://lists.w3.org/Archives/Public/public-houdini/2015Mar/0020.html
[cw-proposal]: https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/Explainer.md

