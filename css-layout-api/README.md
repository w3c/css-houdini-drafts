# CSS Layout API

The CSS Layout API is designed to give authors the ability to write their own layout algorithms in
additon to the native ones user agents ship with today.

For example the user agents currently ship with
 - Block Flow Layout
 - Flexbox Layout

With the CSS Layout API, authors could write their own layouts which implement
 - Constraint based layouts
 - Masonary layouts
 - Line spacing + snapping

### Concepts

##### The `Box`

A `Box` refers to a CSS box, that is a node that has some sort of style. This can refer to:

 - An element with an associated style, (an element that has `display: none` for these purposes does
    not have a style).

 - The `::before` and `::after` pseudo elements with an associated style, (note for layout purposes
    the `::first-letter`, `::first-line`, `::selection` are *not* independent boxes, they are more a
    special kind of selector that can override style on *part* of another box).

 - A `TextNode` with some style.

This is effectively the DOM tree but with some extra things. One important thing to node is that a
`Box` doesn't have any layout information, it is the _input_ to layout.

For the layout API specifically a box is represented like:

```webidl
interface Box {
    readonly attribute StylePropertyMapReadonly styleMap;
    FragmentRequest doLayout(ConstraintSpace space, OpaqueBreakToken breakToken);
};
```

The `styleMap` contains the required computed style for that `Box`.

##### The `Fragment`

A `Fragment` refers to a CSS fragment, that is it is the part of the layout result of a box. This
could be for example:

 - A whole box which has undergone layout. E.g. the result of laying out an `<img>` tag.

 - A portion of a box which has undergone layout. E.g. the result of laying out the first column of
     a multicol layout. `<div style="columns: 3"></div>`

 - A portion of a `TextNode` which has undergone layout, for example the first line, or the first
     portion of a line with the same style.
 
 - The `::first-letter` fragment of a `TextNode`.

One can think of this as the _leaf_ representation you can get out of:
```js
let range = document.createRange();
range.selectNode(element);
console.log(range.getClientRects());
```

For the layout API specifically a fragment is represented like:

```webidl
interface Fragment {
    readonly attribute double inlineSize;
    readonly attribute double blockSize;

    attribute double inlineStart; // inlineOffset instead?
    attribute double blockStart;

    readonly attribute sequence<Box> unpositionedBoxes;

    readonly attribute OpaqueBreakToken? breakToken;

    readonly attribute BaselineOffset dominantBaseline;
    readonly attribute BaselineOffset? ideographicBaseline;
    // other baselines go here.
};
```

### Performing Layout

The Layout API is best described with a simple dummy example:

```js
registerLayout('really-basic-block', class {
    *layout(constraintSpace, children, styleMap, opt_breakToken) {
        let inlineSize = 0;
        let blockSize = 0;
        const childFragments = [];

        for (let child of children) {
            let fragment = yield child.doLayout(constraintSpace);
            blockSize += fragment.blockSize;
            inlineSize = Math.max(inlineSize, fragment.inlineSize);
            childFragments.push(fragment);
        }

        return {
            inlineSize: inlineSize,
            blockSize: blockSize,
            children: childFragments,
        };
    }
});
```

The first thing to notice about the API is that the layout method on the class returns a generator.

TODO finish writing this.
