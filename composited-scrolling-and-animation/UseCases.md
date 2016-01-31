# Compositor Scrolling and Animation Use Cases

Parallax
-----
- the position of elements on the page is related to the scroll position of their container (or maybe another container)
- not a direct link between scroll offset and position. Rather it is some factor, possibly with damping or a curve.
- postion is the most common output, but it could also be opacity or a filter effect such as blur (or really any rendering property)

Scroll header
----
- A header at the top of the document
- When approaching scrollTop=0 header smoothly animates into a more substantial one. Eg. images, opacity, text size animate with scroll position.
- May also only be shown when scrolling down (like hidey bars)
- Examples:
  - The top bar on [Twitter user pages](https://twitter.com/LEGO_Group)
  - Polymer's [core-scroll-header-panel](http://polymer.github.io/core-scroll-header-panel/components/core-scroll-header-panel/demos/demo9.html) and [paper-scroll-header-panel](https://elements.polymer-project.org/elements/paper-scroll-header-panel?view=demo:demo/index.html)

Video sync
-----
- Video whose time point is determined as a function of the scroll offset.
- Must be synced perfectly with scrolling, eg. scrolling down one pixel may advance the video by one frame, and that video frame may move everything up one pixel to counter the scroll.  To the user it must appear as if the content didn't move with the scroll.

Linked scrollers
-----
- Multiple elements are to be scrolled together but possibly at different rates
- Like parallax except not overlapping, use input may occur on any of the linked elements
- One example [here](http://stackoverflow.com/questions/19786080/how-to-synchronize-scroll-between-two-elements-with-different-height).  [AV club](http://www.avclub.com/review/weeknd-navigates-trippy-perception-and-pop-reality-224412) also appears to do this.
- Artificial example [here](http://fiddle.jshell.net/kunknown/VVaEq/2/show/)

Drag and Drop
-----
- The ability to tightly tie the position of an element to touch input.
- A common effect is to have other content move to make space for the dragged content as it is moved about.

Drawers
-----
- Similar to drag and drop, we would like to tie an element to touch input.
- If a draw animation is initiated, we would also like to be able to catch the drawer before the animation completes.
- I.e., we want to be able to immediately interrupt a compositor-driven animation based on input.

Performant Effect Libraries
-----
- Currently, if a library provides an effect that is driven on the main thread, the performance of that effect depends entirely on the performance of the embedding content. It would be valuable to be able to author a library that is more performance isolated and can bill itself as such.

Element Location Tracking
-----
- It would be nice to keep track of the location of an element with respect to another element (in particular, a scroll clip), to get an asynchronous, as-accurate-as-possible set of records of the element's location history.
 

