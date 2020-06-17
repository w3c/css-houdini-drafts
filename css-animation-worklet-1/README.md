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
    *   Hidey-bar ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/twitter-header/)): animation depends on both scroll and time input.
    *   Parallax  ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/parallax-scrolling/)): simplest scroll-driven effect.
    *   Custom paginated slider ([demo](http://aw-playground.glitch.me/amp-scroller.html)).
    *   Pull-to-refresh: animation depends on both touch and time inputs.
    *   Custom scrollbars.
    *   High-fidelity location tracking and positioning
    *   [More examples](https://github.com/w3c/css-houdini-drafts/blob/master/scroll-customization-api/UseCases.md) of scroll-driven effects.
*   Gesture driven effects:
    *   [Image manipulator](https://github.com/w3c/csswg-drafts/issues/2493#issuecomment-422153926) that scales, rotates etc.
    *   Swipe to Action.
    *   Drag-N-Drop.
    *   Tiled panning e.g., Google maps.
*   Stateful script driven effects:
    *   Spring-Sticky effect ([demo](http://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-sticky/)).
    *   Touch-driven physical environments.
    *   Expando ([demo](http://googlechromelabs.github.io/houdini-samples/animation-worklet/expando/)): Procedural animations with multiple elements.
*   Animated scroll offsets:
    * Having multiple scrollers scroll in sync e.g. diff viewer keeping old/new in sync when you
      scroll either ([demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/sync-scroller/))
    * Custom smooth scroll animations (e.g., physic based fling curves)
*   Animation Extensibility:
    *  Custom animation timings (particularly those that are not calculable a priori e.g., [spring demo](https://googlechromelabs.github.io/houdini-samples/animation-worklet/spring-timing/))
    *  Custom animation sequencing which involves complex coordination across multiple effects.


Not all of these usecases are immediately enabled by the current proposed API. However Animation
Worklet provides a powerfull primitive (off main-thread scripted animation) which when combined with
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


# Animation Worklet

Animation Worklet attempts to address the above usecases by introducing a new primitive that enables
extensibility in the web's core animation model [WebAnimations][WA]): custom frame-by-frame animate
function!


## How It Works

Normally, an active animation takes its timeline time and according to its running state (e.g.,
playing, finished) and playback rate, computes its own **current time** which it then uses to set
its keyframe effect **local time**. Here is a simple example of a simple animation:

```js
const effect = new KeyframeEffect(targetEl,
  {transform: ['translateX(0)', 'translateX(50vw)']},
  {duration: 1000}
);
const animation = new Animation(effect, document.timeline);
animation.play();
```


Animation Worklet allows this transformation from **current time** to **local time** to be
customized via a special Javascript function `animate`. Similar to other Houdini worklets, these
animate functions are called inside a restricted [worklet][worklet] context (`AnimationWorkletGlobalScope`)
which means the don't have access to main document. Another implication is that implementor can run
these off-thread to ensure smooth animations even when main thread is busy which is a key
performance goal for animations.

To leverage this machinery, web developer creates a special Animation subclass, `WorkletAnimation`.
The only difference is that the WorkletAnimation constructor takes a `name` argument that identifies
the custom animate function to be used. Animation Worklet then creates a corresponding *animater*
instance that represent this particlar animation and then on each animation frame calls its
`animate` function to determine the local time which ultimately drives the keyframe effect.


![Overview of the WorkletAnimation Timing Model](img/WorkletAnimation-timing-model.svg)

Here the same simple example but using Animation Worklet instead.

**index.html**
```js
// Load your custom animator in the worklet
await CSS.animationWorklet.addModule('animator.js');

const effect = new KeyframeEffect(targetEl,
  {transform: ['translateX(0)', 'translateX(50vw)']},
  {duration: 1000}
);
const animation = new WorkletAnimation('my-awesome-animator', effect);
animation.play();
```

**animator.js**
```
registerAnimator('my-awesome-animator', class Passthrough extends StatelessAnimator {
  animate(currentTime, effect) {
    // The simplest custom animator that does exactly what regular animations do!
    effect.localTime = currentTime;
  }
});
```


A few notable things:

 - WorkletAnimation behaves the same as regular animations e.g., it can be played/paused/canceled
 - WorkletAnimation can optionally accept an options bag to help the corresponding Animator
   configure itself during construction.
 - Animator controls the output of the animation by setting the AnimationEffect.localTime
 - There is two types of Animators: Stateless and Statefull explicitly marked using superclasses.

Below are a few more complex example each trying to show a different aspect of Animation Worklet.

# Examples

## Spring Timing

Here we use Animation Worklet to create animation with a custom spring timing.


```html

<div id='target'></div>

<script>
await CSS.animationWorklet.addModule('spring-animator.js');
targetEl = document.getElementById('target');

const effect = new KeyframeEffect(
  targetEl,
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

Note that ideally once sping simulation is finished, the worklet animation would also dispatch
the `finish` event. Adding the necessary mechanism to enable this is tracked
[here](https://github.com/w3c/css-houdini-drafts/issues/808).

## Twitter Header

Note: This assumes experimental [ScrollTimeline][scroll-timeline] feature.

An example of twitter profile header effect where two elements (avatar, and header) are updated in
sync with scroll offset.

```html

<div id='scrollingContainer'>
  <div id='header' style='height: 150px'></div>
  <div id='avatar'><img></div>
</div>

<script>
const headerEl = document.getElementById('header');
const avatarEl = document.getElementById('avatar');
const scrollingContainerEl = document.getElementById('scrollingContainer');


await CSS.animationWorklet.addModule('twitter-header-animator.js');
const animation = new WorkletAnimation('twitter-header',
  [new KeyframeEffect(avatarEl,  /* scales down as we scroll up */
                      [{transform: 'scale(1)'}, {transform: 'scale(0.5)'}],
                      {duration: 1000, iterations: 1}),
    new KeyframeEffect(headerEl, /* loses transparency as we scroll up */
                      [{opacity: 0}, {opacity: 0.8}],
                      {duration: 1000, iterations: 1})],
    new ScrollTimeline({
      scrollSource: scrollingContainerEl,
      timeRange: 1000,
      orientation: 'block',
      startScrollOffset: 0,
      endScrollOffset: headerEl.clientHeight}),
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

## Swipe-to-Action

Another usecase for Animation Worklet is to enable interactive input-driven animation effects that
are driven both by input events and time.

To enable this we need a way to receive pointer events in worklet (e.g. via [CSS custom
variables](https://github.com/w3c/css-houdini-drafts/issues/869) or [other
mechanisms][input-for-worker]) and
also allow [playback controls](https://github.com/w3c/css-houdini-drafts/issues/808) inside
worklets. Both of these are natural planned additions to Animation Worklet.


Consider a simple swipe-to-action effect which follows the user swipe gesture and when finger lifts
then continues to completion (either dismissed or returned to origin) with a curve that matches the
swipe gesture's velocity. (See this [example](https://twitter.com/kzzzf/status/917444054887124992))

With Animation Worklet, this can be modeled as a stateful animator which consumes both time and
pointer events and have the following state machines:

![SwipeToCompletionAnimation](img/swipe-to-dismiss-state.png)


Here are the three main states:

1. Animation is idle, where it is `paused` so that it is not actively ticking
2. As soon as the user touches down, the animation moves the target to follow the user touchpoint
   while staying `paused` (optionally calculate the movement velocity, and overall delta).
3. As soon as the user lift their finger the animation will the switch to 'playing' so that it is
   ticked by time until it reaches its finished state. The final state may be decided on overall
   delta and velocity and the animation curve adapts to the movement velocity.

Note that while in (3), if the user touches down we go back to (2) which ensures responsiveness to
user touch input.

To make this more concrete, here is how this may be implemented (assuming strawman proposed APIs for
playback controls and also receiving pointer events). Note that all the state machine transitions
and various state data (velocity, phase) and internal to the animator. Main thread only needs to
provide appropriate keyframes that can used to translate the element on the viewport as appropriate
(e.g., `Keyframes(target, {transform: ['translateX(-100vw)', 'translateX(100vw)']})`).


```javascript
registerAnimator('swipe-to-dismiss', class SwipeAnimator extends StatefulAnimator {
  constructor(options, state = {velocity: 0, phase: 'idle'}) {
    this.velocity = state.velocity;
    this.phase = state.phase;

    if (phase == 'idle') {
      // Pause until we receive pointer events.
      this.pause();
    }

    // Assumes we have an API to receive pointer events for our target.
    this.addEventListener("eventtargetadded", (event) => {
     for (type of ["pointerdown", "pointermove", "pointerup"])  {
        event.target.addEventListener(type,onPointerEvent );
     }
    });
  }

  onpointerevent(event) {
    if (event.type == "pointerdown" || event.type == "pointermove") {
      this.phase = "follow_pointer";
    } else {
      this.phase = "animate_to_completion";
      // Also decide what is the completion phase (e.g., hide or show)
    }

    this.pointer_position = event.screenX;

    // Allow the animation to play for *one* frame to react to the pointer event.
    this.play();
  }

  animate(currentTime, effect) {
    if (this.phase == "follow_pointer") {
      effect.localTime = position_curve(this.pointer_position);
      update_velocity(currentTime, this.pointer_position);
      // Pause, no need to produce frames until next pointer event.
      this.pause();
    } else if (this.phase = "animate_to_completion") {
      effect.localTime = time_curve(currentTime, velocity);

      if (effect.localTime == 0 || effect.localTime == effect.duration) {
        // The animation is complete. Pause and become idle until next user interaction.
        this.phase = "idle";
        this.pause();
      } else {
        // Continue producing frames based on time until we complete or the user interacts again.
        this.play();
      }
    }

  }

  position_curve(x) {
    // map finger position to local time so we follow user's touch.
  }

  time_curve(time, velocity) {
    // Map current time delta and given movement velocity to appropriate local time so that over
    // time we animate to a final position.
  }

  update_velocity(time, x) {
    this.velocity = (x - last_x) / (time - last_time);
    this.last_time = time;
    this.last_x = x;
  }

  state() {
    return {
      phase: this.phase,
      velocity: this.velocity
    }
  }
});
```

```javascript

await CSS.animationWorklet.addModule('swipe-to-dismiss-animator.js');
const target = document.getElementById('target');
const s2d = new WorkletAnimation(
    'swipe-to-dismiss',
    new KeyframeEffect(target, {transform: ['translateX(-100vw)', 'translateX(100vw)']}));
s2d.play();
```


# Why Extend Animation?

In [WebAnimation][WA], [Animation][animation] is the main controller. It handles the playback commands
(play/pause/cancel) and is responsible for processing the progressing time (sourced from Timeline) and
driving keyframes effect which defines how a particular target css property is animated and
ultimately pixels moving on the screen.

By allowing extensibility in Animation we can have the most flexibility in terms of what is possible
for example animation can directly control the following:
 - Control animation playback e.g., implement open-ended animations with non-deterministic  timings
   (e.g., physical-based) or provide "trigger" facilities
 - Flexibility in transforming other forms of input into "time" e.g., consume touch events and drive
   animations
 - Ability to handle multiple timelines e.g., animations that seamlessly transition btween being
   touch/scroll driven to time-driven
 - Control how time is translated e.g., new custom easing functions
 - Drive multiple effects and control how they relate to each other e.g., new effect sequencing


While there is benefit in extensibility in other parts of animation stack (custom timeline, custom
effect, custom timing), custom animations provides the largest value in terms of flexibility and
addressing key usecases so it is the one we are tackling first.

Animation Worklet can be easily augmented in future to support other Houdini style extensibility
features as well.


TODO:  Also discuss other models that we have considered (e.g., CompositorWorker) that bypassed
web animation altogether.



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
    }
  }

  curve(velocity, accerlation, t) {
     return /* compute some physical movement curve */;
  }
});
```


## Threading Model

Animation Worklet is designed to be thread-agnostic. Rendering engines may create one or more
parallel worklet execution contexts separate from the main javascript execution context, e.g., on
their own dedicated threads. Rendering engines may then choose to assign Animation Worklet
animations to run in such contexts. Doing so allows Animation Worklet animations to avoid being
impacted by main thread jank.

Rendering engines may wish to make a best-effort attempt to execute animate callbacks synchronously
with visual frame production to ensure smooth animation. However it is legal for rendering engines
to produce visual frames without blocking to receive animation updates from a worklet (i.e., letting
the effects slip behind). For example, this could occur when the animate function callback is
unable to complete before the frame deadline.

We believe that scripted animations which are run in a parallel execution environment and which
limit themselves to animating properties which do not require the user agent to consult main thread
will have a much better chance of meeting the strict frame budgets required for smooth playback.


Note that due to the asynchronous nature of this animation model a script running in the main
javascript execution context may see a stale value when reading a target property that is
being animated in a Worklet Animation, compared to the value currently being used to produce the
visual frame that is visible to the user. This is similar to the effect of asynchronous scrolling
when reading scroll offsets in the main javascript execution context.


<figure>
  <img src="img/AnimationWorklet-threading-model.svg" width="600"
    alt="Overview of the animation worklet threading model.">
  <figcaption>
    Overview of the animation worklet threading model. <br>

    A simplified visualization of how animators running in a parallel execution environment can sync
    their update to main thread while remaining in sync with visual frame production.
  </figcaption>
</figure>


# Related Concepts

The following concepts are not part of Animation Worklet specification but Animation Worklet is
designed to take advantage of them to enable a richer set of usecases. These are still in early
stages of the standardization process so their API may change over time.

## ScrollTimeline
[ScrollTimeline][scroll-timeline] is a concept introduced in
scroll-linked animation proposal. It defines an animation timeline whose time value depends on
scroll position of a scroll container. `ScrollTimeline` can be used an an input timeline for
worklet animations and it is the intended mechanisms to give read access to scroll position.

We can later add additional properties to this timeline (e.g., scroll phase (active, inertial,
overscroll), velocity, direction) that can further be used by Animation Worklet.

## GroupEffect

[GroupEffect][group-effect] is a concept introduced in Web Animation Level 2 specification. It
provides a way to group multiple effects in a tree structure. `GroupEffect` can be used as the
output for Worklet Animations making it possible for it to drive complext effects spanning multiple
elements. Also with some minor [proposed changes](group-effect-changes) to Group Effect timing
model, Animation Worklet can enable creation of new custom sequencing models (e.g., with conditions
and state).

## Event Dispatching to Worker and Worklets
[Event Dispatching to Worker/Worklets][input-for-worker] is a proposal in WICG which allows workers
and worklets to passively receive DOM events and in particular Pointer Events. This can be
benefitial to Animation Worklet as it provides an ergonomic and low latency way for Animation
Worklet to receive pointer events thus enabling it to implement input driven animations more
effectively.


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
[WA]: https://drafts.csswg.org/web-animations/
[animation]: https://drafts.csswg.org/web-animations/#animations
[worklet]: https://drafts.css-houdini.org/worklets/#worklet-section
[input-for-worker]: https://discourse.wicg.io/t/proposal-exposing-input-events-to-worker-threads/3479
[group-effect]: https://w3c.github.io/web-animations/level-2/#the-animationgroup-interfaces
[group-effect-changes]: https://github.com/yi-gu/group_effects
[scroll-timeline]: https://wicg.github.io/scroll-animations/#scrolltimeline