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
 

