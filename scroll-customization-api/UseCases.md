
The [Composited Scrolling](https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/UseCases.md) use cases include effects that respond to and are synchronized with scroll position.  Below are additional use cases which require more control over exactly how scrolling behaves.

Hidey bars
----
- Similar to a [Scroll header](https://github.com/w3c/css-houdini-drafts/blob/master/composited-scrolling-and-animation/UseCases.md#scroll-header) 
- Typically have a different effect depending on the direction of scroll, and depending on whether they are attached to the top or bottom of their scroll area
 - e.g. scrolling down the bar moves with the container, and disappears outside the bounds
- scrolling up, the bar animates in with a timed animation. It's position is relative to its container at this point.
- When a scroll operation ends (eg. fingers lifted from touchpad), may animate to either fully shown or fully hidden
- Advanced: content may “hide” into a smaller version of itself, that is sticky positioned (e.g. iPhone Safari URL bar)
- Advanced: may resize the contents after showing / hiding (eg. so that contents scrollbar stops below the header, and elements can be reliably position:fixed to the top of the contents). 
- Examples:
 - Top controls in mobile browsers like Chrome for Android and Mobile Safari

Rubber banding
----
- scroll is normal until it hits limits (input scroll amount -> output scroll amount)
- after that point, scroll output is a fraction of the input (input * factor -> output)
- upon release, animate back to limit
- also should work with a momentum deceleration (if the user has flicked far enough to hit the limits)

Snap points
----
- Scrolling as normal during the normal scroll phase
- But when the scroll ends (eg. after finger lift), animates to a well-defined boundary 
- Example
 - [CSS Snap points](https://drafts.csswg.org/css-snappoints/), and earlier [IE/Edge implementation](https://msdn.microsoft.com/en-us/library/windows/apps/hh466031.aspx)

Pull to refresh
----
This is one of the more tricky effects.

- Implemented with a rubber band effect
- Allows drawing into the background of the container, with fixed position, giving the illusion of it being in the negative margin of the scrolling object
 - Often the effect is coupled to the scroll position (eg. a circle that rotates in proportion to the scroll position).  There's a wide variety of different effects here.
- Has a threshold in the rubber band, at which point the refresh "commits". This typically triggers another animation, where the content stays where it was (its rubber-band limit) and a progress spinner is drawn in the margin. Do we consider this as if the scroll has ended and the content has moved down?
- Once the page has the refreshed data, it adds it to the DOM (causing another scroll). Or if there wasn't any data, the content animates back to the top of the container.
- Can transition into and out-of the overscroll effect without lifting the finger
- Can fling into the overscroll effect ("peek")
- Can fling out of the overscroll effect
- Scroll targeted correctly for spring physics.  Effectively, the spring "captures" the scroll impulse first when collapsing and last when expanding. 
  - Eg. If you place your finger inside an iframe within a document with p2r while the header is showing, target the p2r document if the scroll would collapse the header, but target the iframe if the scroll would expand the header.
  - In browsers without scroll latching, scrolling an iframe inside a document with p2r, pull UI starts to show, finger direction is reversed, now pull UI needs to collapse in preference is scrolling the iframe.  
  - Scrolling an iframe with p2r inside of a normal document, when the limit of the iframe is reached first, the document scrolls, and only when that limit is reached does the spring effect begin (in our prototypes, anything else feels like broken physics).
- Pull to refresh must compose properly with snap points.

This means the effect has a number of inputs and outputs.
input: the scroll value, the limit of the rubber band
output: the final scroll position, control over the refresh drawing animation, the ability to move the content by a certain amount, the ability to cancel the effect

Custom scrollers
-----
- Rather than just translate the content on scroll, do something flashier like a 3D transform
- See libraries like [ContentFlow](http://www.jacksasylum.eu/ContentFlow/) 
- A great solution needs to chain to/from nested scrollers exactly as other scrollers do
- One particular example I've seen that feels really nice (but can't find a public demo of) is a sort of physics simulation where each item (image, panel, card, etc.) moves as if there's a (dampened) spring connecting it to it's neighbors.  Eg. when scrolling fast there is more separation between items.  As soon as you stab an item to stop it scrolling, the other items kind of bounce into it and settle at a nice distance away.

Re-targeting scrolling
-----
- A scroll occurring over one point in the document is redirected to cause scrolling somewhere else.
- Eg. GMail does this in conversation view - scroll on the right hand side (which isn't itself scrollable) and they scroll the conversation.  They do this by listening for wheel events, but this doesn't work for touch.
 
Disable scroll chaining
-----
- Ability for an element to prevent scrolling from propagating up to an ancestor
- Eg. Facebook chat widget (or any position:fixed overlay window)
  - position: fixed container with an overflow:scroll div inside
  - When the scroller has scrollTop=0, user attempting to scroll up on top of the widget should NOT cause the document to scroll
- Similar to IE/Edge's [-ms-scroll-chaining](https://msdn.microsoft.com/en-us/library/windows/apps/hh466007.aspx) except that effects only the chaining that occurs during a scroll gesture.  The use case here may want to disable chaining even at the start of a new scroll gesture.

Custom scroll limit
-----
- Limit scrolling to a sub-region of the scrollable area
- IE/Edge has [-ms-scroll-limit](https://msdn.microsoft.com/en-us/library/jj127336(v=vs.85).aspx)
- I'm actually not sure of the real-world use case for this, but I'm sure the IE team had one.  Perhaps @atanassov can enlighten us?

Custom overscroll effect
-----
- When reaching the scroll limit, draw a custom effect indicating how far beyond the limit scrolling is being attempted
- Takes scroll fling behavior into account.  May also take precise finger position into account (eg. horizontal position in a vertical-scroll-only scroller) when drawing the effect
- Example: native scroll behavior on Android ("blue glow" pre Android L, "scroll tongue" post Android L).

Other examples (combined effects)
----
http://www.nytimes.com/interactive/2014/09/19/travel/reif-larsen-norway.html
(fading, snap points, video/animation sync)

http://www.nytimes.com/projects/2013/gun-country/
(snap points, video sync)

http://www.nytimes.com/projects/2013/the-jockey/
(fading, snap points, video/animation sync, sticky positioning...)
Note the interesting pull quotes that combine it all.

http://www.nytimes.com/projects/2013/tomato-can-blues/
(parallax, sticky positioning, progressively-insert-and-move-things, 

http://www.nytimes.com/projects/2012/snow-fall/
(automatic scrolling, fading, video/animation sync, sticky positioning)

