# Implementation Status

## Chrome

This is a rough sketch of how Chrome plans to deliver Animation Worklet features:

1.  Animation Worktlet Prototype (done): scripted custom animation, single effect, only fast
    properties, off-thread.
2.  Animation Worktlet [Origin Trial][ot-blogpost] (in progress, [signup][ot-signup]): good
    performance, scroll input (ScrollTimeline), basic web-animation controls (play/cancel).
3.  Animation Worktlet MVP (in development): animate all properties (slow path ones running in sync
    with main thread), multiple effects (i.e., GroupEffect), full web-animation integration.
4.  Animation Worktlet V2 (future): touch/gesture input, multiple inputs in single animation,
    sophisticated scheduling, other outputs.

[ot-blogpost]: https://developers.google.com/web/updates/2018/10/animation-worklet
[ot-signup]:https://docs.google.com/forms/d/e/1FAIpQLSfO0_ptFl8r8G0UFhT0xhV17eabG-erUWBDiKSRDTqEZ_9ULQ/viewform

