

## Hidey bars
- typically have a different effect depending on the direction of scroll, and depending on whether they are attached to the top or bottom of their scroll area
- e.g. scrolling down the bar moves with the container, and disappears outside the bounds
- scrolling up, the bar animates in with a timed animation. It's position is relative to its container at this point.
- When a scroll operation ends (eg. fingers lifted from touchpad), may animate to either fully shown or fully hidden
- Advanced: content may “hide” into a smaller version of itself, that is sticky positioned (e.g. iPhone Safari URL bar)

## Scroll header

- A header at the top of the document
- When approaching scrollTop=0 header smoothly animates into a more substantial one. Eg. images, opacity, text size animate with scroll position.
- May also only be shown when scrolling down (like hidey bars)
- Examples:
  - The top bar on [Twitter user pages](https://twitter.com/LEGO_Group)
  - Polymer's [core-scroll-header-panel](http://polymer.github.io/core-scroll-header-panel/components/core-scroll-header-panel/demos/demo9.html) and [paper-scroll-header-panel](https://elements.polymer-project.org/elements/paper-scroll-header-panel?view=demo:demo/index.html)
  - Rubber banding

## Pull to refresh

## Parallax

## Custom scrollers

## Re-targeting scrolling

## Linked scrollers

## Disable scroll chaining

## Custom scroll limit

## Custom overscroll effect
