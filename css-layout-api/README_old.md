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

This document aims to give a high level overview to the Layout API.

### Concepts

##### The `Box`

A `Box` refers to a CSS box, that is a node that has some sort of style. This can refer to:

 - An element with an associated style, (an element that has `display: none` for these purposes does
    not have a style).

 - The `::before` and `::after` pseudo elements with an associated style, (note for layout purposes
    the `::first-letter`, `::first-line`, `::selection` are *not* independent boxes, they are more a
    special kind of selector that can override style on *part* of another box).

 - A `TextNode` with some style.

This is effectively the DOM tree but with some extra things. One important thing to note is that a
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

One important thing to note is that you can't change the `inlineSize` or `blockSize` of a fragment
once have received it from a child layout. The _only_ thing you can change is its position (with
`inlineStart` or `blockStart`) relative to the parent.

See below for a description of baselines.

The `unpositionedBoxes` attribute is a list of `Box`es which couldn't be positioned by the child.
The current layout can choose to layout and position these, or it can pass them up to its parent.

#### The `ConstraintSpace`

A `ConstraintSpace` is a 2D representation of the layout space given to a layout. A constraint space
has:
 - A `inlineSize` and `blockSize`. If present, these describe a fixed width in which the layout can
    produce a `Fragment`. The layout should produce a `Fragment` which fits inside these bounds. If
    it exceeds these bounds, the `Fragment` may be paint clipped, etc, as determined by its parent.

 - A `inlineScrollOffset` and `blockScrollOffset`. If present, these describe that if the resulting
    `Fragment` exceeds these offsets, it must call `willInlineScroll()` / `willBlockScroll()`. This
    will result in the constraint space being updated (and also reset to its initial state?). These
    methods will potentially change the `inlineSize` or `blockSize` to allow room for a scrollbar.

 - A `inlineFragmentOffset` and `blockFragmentingOffset`. If present, these describe that if the
   resulting `Fragment` must fragment at this particular point.

 - A list of exclusions. Described more in-depth below.

The `ConstraintSpace` is represented as:

```webidl
partial interface ConstraintSpace {
    readonly attribute double? inlineSize;
    readonly attribute double? blockSize;

    readonly attribute double? inlineScrollOffset;
    readonly attribute double? blockScrollOffset;

    readonly attribute double? inlineFragmentOffset; // Is inline fragment offset needed?
    readonly attribute double? blockFragmentOffset;

    void willInlineScroll();
    void willBlockScroll();
};
```

This may be better represented as:

```webidl
partial interface ConstraintSpace {
    readonly attribute ExtentConstraint inlineConstraint;
    readonly attribute ExtentConstraint inlineConstraint;

    void willInlineScroll();
    void willBlockScroll();
};

enum ExtentConstraintType = 'fixed' | 'scroll' | 'fragment';

interface ExtentConstraint {
  readonly attribute ExtentConstraintType type;
  readonly attribute double offset;
};
```

| Actually this doesn't really work? As you can have an inlineSize, which also can overflow. |
| --- |

Exclusions can be added to the constraint space which children should avoid. E.g.

```webidl
partial interface ConstraintSpace {
    void addExclusion(Fragment fragment, optional FlowEnum flow);
    void addExclusion(Exclusion fragment, optional FlowEnum flow);
    readonly attribute sequence<Exclusion> exclusions;
};

dictionary Exclusion {
    double inlineSize;
    double blockSize;

    double inlineStart;
    double blockStart;

    double inlineEnd;
    double blockEnd;
};
```

The author can iterate through the available space via the `layoutOpportunities()` api.

```webidl
partial interface ConstraintSpace {
    Generator<LayoutOpportunity> layoutOpportunities();
};

interface LayoutOpportunity {
    readonly attribute double inlineSize;
    readonly attribute double blockSize;

    readonly attribute double inlineStart;
    readonly attribute double blockStart;

    readonly attribute double inlineEnd;
    readonly attribute double blockEnd;
}
```

Here is a cute little gif which shows the layout opportunities for a `ConstraintSpace` with two
exclusions.

![layout opportunities](https://raw.githubusercontent.com/w3c/css-houdini-drafts/master/images/layout_opp.gif)

The layoutOpportunities generator will return a series of max-rects for a given constraint space.
These are ordered by `inlineStart`, `inlineSize` then `blockStart`.

| How do we represent non-rect exclusions? Initial thought is to always jump by `1em` of author |
| specified amount. |
| --- |

###### Advanced exclusions

Not everything in CSS avoids all exclusions. For example:

![inline text avoiding floats](https://raw.githubusercontent.com/w3c/css-houdini-drafts/master/images/exclusions_1.png)

The green block-level element doesn't avoid the intruding floats, but its inline-level children do.

Should authors be able to annotate exclusions with a tag, then just `LayoutOpportunities` based on
those tags? For example:

```webidl
partial interface ConstraintSpace {
  void addExclusion(Fragment exclusion, optional FlowEnum flow, optional sequence<DOMString> tags);

  // calling layoutOpportunities(['left']), only provides layout opportunities which avoids
  // exclusions tagged with left.
  Generator<LayoutOpportunity> layoutOpportunities(optional sequence<DOMString> tags);
};
```

#### Breaking and `BreakToken`s

TODO write about how break tokens work.

#### Pseudo-elements and style overrides

`::first-letter` and `::first-line` are a little bit special in terms of CSS; they aren't really
elements just a different style applied to a fragment(s).

In order to handle these do we allow override styles when performing layout on a child? For example:
```webidl
partial interface Box {
    FragmentRequest doLayout(ConstraintSpace space, OpaqueBreakToken breakToken, Object overrideStyles);
}
```

```js
registerLayout('handle-first-line', class {
    *layout(constraintSpace, children, styleMap, opt_breakToken) {
        // ...

        let child = children[i];
        let fragment = yield child.doLayout(childConstraintSpace, breakToken, {
            // This would be queried from styleMap?
            // This would only allow computed-style values?
            fontSize: new CSSLengthValue({px: 18}),
        });

        // ...
    }
});
```

TODO: These is a problem with the above example?

Similarly we have a class of CSS layout algorithms which _force_ a particular style on their
children, (flex & grid). Do we handle these in a similar way? For example:

```js
registerLayout('kinda-like-flex', class {
    *layout(constraintSpace, children, styleMap, opt_breakToken) {
        // ...

        let child = children[i];
        let fragment = yield child.doLayout(childConstraintSpace, breakToken, {
            inlineSize: 180, // Only accepts numbers in px.
        });

        // ...

    }
});
```

We need something like this, needs to be here, or on the constraintSpace somehow.

#### Utility functions

We need a set of utility function which do things like resolve a computed-inline-size against
another length etc. These functions will probably become clear over-time from internal
implementations and people writing algorithms against this API but for starters we'll probably need:

```webidl
[NoInterfaceObject]
interface LayoutUtilities {
    // Resolves the inline-size according to an algorithm to be defined in the spec. This doesn't
    // limit authors to having their own layout units and resolving the lengths differently. This is
    // just a helper.
    number resolveInlineSize(ConstraintSpace constraintSpace, StylePropertyMapReadonly styleMap);

    // Resolves the size against a different length.
    number resolveSize(CSSValue property, number size);

    // Resolves the size against a different length for the minimum amount.
    number resolveMinimumSize(CSSValue property, number size);
}
```

This is just some basic ones, we'll need more.

#### Flags!

We need to indicate to the engine when we want a particular layout behaviour placed on us. For
example if we are a:
 - formatting context
 - should "blockify" children (like flex, grid)
 - magically handle abs-pos

TODO there are probably others here.

For example if we should establish a formatting context, implicitly this means that the
constraintSpace we are given cannot have any pre-defined exclusions.

We need to decide on the defaults here, and if we allow changing the default.

A simple API proposal:
```js
registerLayout('weee!', class {
    static formattingContext = false; // default is true?
    static handleAbsPos = false; // default is true?
    static blockifyChildren = true; // default is false?

    *layout() {
        // etc.
    }
});
```

#### Adding and removing children

We need a callback for when child boxes are added / removed. Rendering engines today have
optimizations in place for when this occurs; for example in grid, the user agent will place its
children into a "Tracks" data structure for layout.

TODO: add API proposal here.

#### Baselines

TODO: add explaination why we need a more powerful API than just offset here.

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
            
            // Position the new fragment.
            fragment.inlineStart = 0;
            fragment.blockStart = blockSize;
            blockSize += fragment.blockSize;
            
            // Add it as an exclusion to the constraintSpace
            constraintSpace.addExclusion(fragment, 'block-end');
            
            // Update the running totals for our size.
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
This is to allow two things:
 1. User agents implementing parallel layout.
 2. User agents implementing asynchronous layout.

The generator returns a `FragmentRequest`. Inside of the authors layout funciton, this object is
completely opaque. This is a token for the user-agent to perform layout _at some stage_ for the
particular box it was generated for.

When a `FragmentRequest` is returned from the generator, the user-agent needs to produce a
`Fragment` for it, and return it via. the generator `next()` call.

As a concrete example, the user agent could implement the logic driving the author defined layout
as:

```js
function performLayout(constraintSpace, box) {
  // Get the author defined layout instance.
  const layoutInstance = getLayoutInstanceForBox(box);
  
  // Access the generator returned by *layout();
  const layoutGenerator = layoutInstance.layout(constraintSpace, box.children, box.styleMap);
  
  // Loop through all of the fragment requests.
  let fragmentRequestObj = layoutGenerator.next();
  while (!fragmentRequestObj.done) {
    const fragmentRequest = [];
    const fragmentResult = [];
    
    // Coorce fragmentRequestObj into an array.
    if (fragmentRequestObj.value.length) {
      fragmentRequest.push(...fragmentRequestObject.value);
    } else {
      fragmentRequest.push(fragmentRequestObject.value);
    }

    for (let i = 0; i < fragmentRequest.length; i++) {
      fragmentResult.push(performLayout(fragmentRequest[i]));
    }
    
    // Request the next fragment.
    fragmentRequestObj = layoutGenerator.next(
      fragmentResult.length == 1 : fragmentResult[0] : fragmentResult);
  }
  
  // The last value from the generator should be the final return value.
  const fragmentDict = fragmentRequest.value;
  return new Fragment(fragmentDict);
}
```

### Example layout algorithms

```js
// 'multicol' does a simple multi-column layout.
registerLayout('multicol', class {
    *layout(constraintSpace, children, styleMap, opt_breakToken) {
        const inlineSize = resolveInlineSize(constraintSpace, styleMap);

        // Try and decide the number of size of columns.
        const columnCountValue = styleMap.get('column-count');
        const columnInlineSizeValue = styleMap.get('column-width');

        let columnCount = 1;
        let columnInlineSize = inlineSize;

        if (columnCountValue) {
          columnCount = columnCountValue.value;
        }

        if (columnInlineSizeValue) {
          columnInlineSize = resolveSize(columnInlineSizeValue, inlineSize);
        }

        if (constraintSpace.inlineScrollOffset &&
            columnInlineSize * columnCount > constraintSpace.inlineScrollOffset) {
          // NOTE: under this condition, we need to start again to re-resolve lengths?
          constraintSpace.willInlineScroll();
          return; // Or just continue here?
        }

        // Create a constraint space which is just the inlineSize of the column.
        const colConstraintSpace = new ConstraintSpace({
            inlineSize: columnInlineSize
        });

        // Perform layout on all the children, taking into account the children
        // which may fragment in the inline direction.
        const childFragments = [];
        let childBlockSize = 0;
        let layoutOpp;
        for (let child of children) {
            let breakToken;
            do {
                const fragment = yield child.doLayout(colConstraintSpace, breakToken);
                breakToken = fragment.breakToken;

                const gen = colConstraintSpace.layoutOpportunities();

                layoutOpp = gen.next().value;
                if (layoutOpp.inlineSize < fragment.inlineSize()) {
                    layoutOpp = gen.next().value;
                }

                fragment.inlineStart = opp.inlineStart;
                fragment.blockStart = opp.blockStart;
                colConstraintSpace.addExclusion(fragment, 'inline-flow');

                childFragments.push(fragment);
            } while (breakToken);
        }

        // FIXME: This might be wrong, need a helper method on constraintSpace which returns the max
        // blockEnd of all the exclusions.
        const childBlockSize =
            colConstraintSpace.layoutOpportunities().next().value.blockStart;

        // Next, a clever person would nicely balance the columns, we are going
        // to do something really simple. :)
        const columnBlockSize = Math.ceil(childBlockSize / columnCount);
        const columnGap = resolveSize(styleMap.get('column-gap'), inlineSize);
        let size = 0;
        let columnNum = 0;
        let columnEndOffset = 0;
        for (let fragment of childFragments) {
            if (size && fragment.blockSize + size > columnBlockSize) {
                size = 0;
                columnNum++;
                columnEndOffset += size;
            }

            fragment.inlineStart += columnNum * (columnGap + columnInlineSize);
            fragment.blockStart -= columnEndOffset;
            size = Math.max(size, fragment.blockStart + fragment.blockSize);
        }

        const blockSize =
            resolveBlockSize(constraintSpace, styleMap, columnBlockSize);

        return {
            inlineSize: inlineSize,
            blockSize: blockSize,
            fragments: childFragments,
        };
    }
});
```
