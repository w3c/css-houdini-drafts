# Animation Worklet Explainer
---

# Key Concepts

## Creating and using a worklet animation

```js
animationWorklet.addModule('twitter-header-animator.js').then( _ => {
  var anim = new WorkletAnimation('twitter-header',
    [
      new KeyFrameEffect($avatarEl,
                         [{ transform: 'translateX(100px)'}, {transform: 'translateX(0px)'}],
                         {duration: 100, iterations: infinite }),
      new KeyFrameEffect($headerEl,
                         { opacity: 0, opacity: 1 },
                         {duration: 100})
    ],	[
      document.timeline,
      // ScrollTimeline: https://wicg.github.io/scroll-animations/#scroll-timelines
      new ScrollingTimeline(scrollingElement, {timeRange: 100})
    ],
    {
      some_awesome_data: 42
    }
  );

  // Same instance shared by animation targets
  anim == $avatarEl.getAnimations()[0] == $headerEl.getAnimations()[0];
});

```

twitter-header-animator.js:
```js
registerAnimator('twitter-header', class {

  constructor(options) {
    // options == { some_awesome_data: 42 }
  }

  animate(timelines, outputEffects) {
    const time = timelines[1].currentTime; // [0...timeRange]
    // drive the output effects by setting their local times.
    outputEffects[0].localTime = time;  // Sets the time used in the first output effect.
    outputEffects[1].localTime = Math.min(1, time * 10); // Clamps the input time range.
    // TODO: at some point allow querying the Effect current value. This is needed for
    // effects where output of one effects affects others.
  }

  // If reverse is provided, allows developer to customize reversing.
  // Default behavior is to
  reverse(timelines) {
    this.reversingFrom = timelines[0].currentTime;
  }

  dispose() {
   // gives a chance to animator to provide option to be used when it needs
   // to be restarted in a different thread/context. This way stateful animations
   // can be migrated safely.
    return this.options;
  }

  update(options) {
    // this is a V2 concept,
  }

});

```


### Notes

 * What should happen if an animation is created before the animator is registered?
 * Should the document.timeline be updated to offset by startTime & scale by playbackRate?
 * What is the behavior

## WEB IDL

We simply create a new BaseAnimation class which holds the basic concepts.
WorkletAnimation and Animation inherit from that. Difference is in the number of
timelines and effects that each support.

Effect gets a writable localTime which may be used to drive the effect from
the worklet.

```webidl
interface BaseAnimation :  EventTarget{
             attribute DOMString                id;
             attribute double?                  startTime;
             attribute double?                  currentTime;
             attribute double                   playbackRate;
    readonly attribute AnimationPlayState       playState;
    readonly attribute Promise<Animation>       ready;
    readonly attribute Promise<Animation>       finished;
             attribute EventHandler             onfinish;
             attribute EventHandler             oncancel;
    void cancel ();
    void finish ();
    void play ();
    void pause ();
    void reverse ();
};


[Constructor (optional AnimationEffectReadOnly? effect = null,
              optional AnimationTimeline? timeline)]
interface Animation :  BaseAnimation {
             attribute AnimationEffectReadOnly? effect;
             attribute AnimationTimeline?       timeline;
};

// Maybe we should return first timeline and first effect as default effect and
// make this just sub-class animation?

[Constructor (DOMString animatorId,
              optional array<AnimationEffectReadOnly>? effects = null,
              optional array<AnimationTimeline>? timelines,
              optional WorkletAnimationOptions)]
interface WorkletAnimation : BaseAnimation {
        attribute array<AnimationTimeline> timelines;
        attribute AnimationEffectReadOnly? effects;
}

[Constructor ((Element or CSSPseudoElement)? target,
              object? keyframes,
              optional (unrestricted double or KeyframeEffectOptions) options),
 Constructor (KeyframeEffectReadOnly source)]
interface KeyframeEffect : KeyframeEffectReadOnly {
    inherit attribute Animatable?                 target;
    inherit attribute IterationCompositeOperation iterationComposite;
    inherit attribute CompositeOperation          composite;
    void setKeyframes (object? keyframes);

    [Exposed=AnimationWorklet]
    attribute localTime; // can be used to drive the effect from inside Worklet

};

```


## Updating Elements

For some effects we need to be able to add new participating elements without
restarting the effect. Here are some thoughts on how this can work.

```js
// Effects and data can change after some time.
// We might want to break this out into separate functions or optional
// updates so you can just update options or just effects and options
// without having to pass other parameters again.
anim.update({
    [ /* new list of effects? */],
    [ /* new list of timelines */],
    {/* options */}
});
```

## CSS Notation

We are not proposing including this in the initial spec, but including some
preliminary thoughts here so that we can keep the eventual declarative CSS
specification in mind.

index.html:
```html
<-- animator instance is declared here, with its timelines -->
<div id="main">
  <-- effect timing is declared here and assigned to above animator -->
  <div class="avatar"></div>
  <div class="header"></div>
  <div class="header"></div>
<div>
```

style.css:
```css
#main {
  animation: worklet('twitter-header')
  animation-timeline: scroll(#scroller_element.....) /* https://wicg.github.io/scroll-animations/#animation-timeline */
}

/* These are descendants of the animation */
#main .header {
  animation-group: 'twitter-header' 'header' <keyframe animation1> <options1> #...
  /* This syntax should be similar to what the plan is for Web Animation Group Effects */
}

#main .avatar {
  animation-group: 'twitter-header' 'avatar' <keyframe animation2> <options2> #...
}
```

This is equivalent to calling:

```js
new WorkletAnimation('twitter-header',
  [
    new KeyFrameEffect(.header[0], [<keyframe animation1>], {<options1>}),
    new KeyFrameEffect(.avatar,    [<keyframe animation2>], {<options2>}),
    new KeyFrameEffect(.header[1], [<keyframe animation1>], {<options1>}),
  ],
  [new ScrollingTimeline(#selector, {...})],
  { elements: [
    /* This is admittedly a bit magical. */
    {'name': 'header'},
    {'name': 'avatar'},
    {'name': 'header'},
  ]}
).play();

```

Adding new elements that match the selector will be
equivalent to invoking `update`.
