# Open API Questions
---


## Creation/Registration timing

What should happen if an animation is created before the animator is registered?

## Timelines

* observe-only timelines? i.e., have access to timeline but the animate is not triggered when its
  value changes.

* Should we have a Timeline.currentTime and Timeline.localTime, where the latter is
  the former but offset by startTime & scaled by playbackRate?

* Access to the actual scroll position in the ScrollTimeline

* Access to scroll phase (inactive, active, inertial etc.)


## Updating Elements

For some effects we need to be able to add new participating elements without
restarting the effect. Here is an initial idea on how this can work.

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

```js
// In worklet scope
class MyAnimator{
  update(options) {
    // this is a V2 concept,
  }
}
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

Adding new elements that match the selector will be equivalent to invoking `update`.
