CSS Layout API Explained
========================

The CSS Layout API is being developed to improve the extensibility of CSS.

Specifically the API is designed to give web developers the ability to write their own layout
algorithms in addition to the native algorithms user agents ship with today.

For example user agents today currently ship with:
 - Block Flow Layout
 - Flexbox Layout

However with the CSS Layout API web developers could write their own layouts which implement:
 - Constraint based layouts
 - Masonry layouts
 - Line spacing and snapping

Initial Concepts - Writing Modes
--------------------------------

This API uses terminology which may be foreign to many web developers initially. Everything in the
CSS Layout API is computed in the [logical coordinate
system](https://drafts.csswg.org/css-writing-modes-3/#text-flow).

This has the primary advantage that when you write your layout using this system it will
automatically work for writing modes which are right-to-left (e.g. Arabic or Hebrew), or for writing
modes which are vertical (many Asian scripts including Chinese scripts, Japanese and Korean).

For a developer who is used to left-to-right text, the way to translate this back into "physical"
coordinates is:

| Logical     | Physical |
| -----------:|:-------- |
| inlineSize  | width    |
| inlineStart | left     |
| inlineEnd   | right    |
| blockSize   | height   |
| blockStart  | top      |
| blockEnd    | bottom   |

Getting Started
---------------

First you'll need to add a module script into the layout worklet.

```js
if ('layoutWorklet' in CSS) {
  await CSS.layoutWorklet.addModule('my-layout-script.js');
  console.log('layout script installed!');
}
```

See the worklets [explainer](../worklets/EXPLAINER.md) for a more involved explanation of worklets.

After the promise returned from the `addModule` method resolves the layouts defined in the script
will apply to the page.

A Centering Layout
------------------

The global script context for the layout worklet has exactly one entry method exposed to developers:
`registerLayout`.

There are a lot of things going on in the following example so we'll step through them one-by-one
below. You should read the code below with its explanatory section.

```js
registerLayout('centering', class {
  async layout(children, edges, constraints, styleMap) {
    // (1) Determine our (inner) available size.
    const availableInlineSize = constraints.fixedInlineSize - edges.inline;
    const availableBlockSize = constraints.fixedBlockSize ?
        constraints.fixedBlockSize - edges.block :
        null;

    let maxChildBlockSize = 0;

    const childFragments = [];
    for (let child of children) {
      // (2) Perform layout upon the child.
      const fragment = await child.layoutNextFragment({
          availableInlineSize,
          availableBlockSize,
      });

      // Determine the max fragment size so far.
      maxChildBlockSize = Math.max(maxChildBlockSize, fragment.blockSize);

      // Position our child fragment.
      fragment.inlineOffset = edges.inlineStart +
                              (constraints.fixedInlineSize - fragment.inlineSize) / 2;
      fragment.blockOffset = edges.blockStart +
                             Math.max(0, (constraints.fixedBlockSize - fragment.blockSize) / 2);

      childFragments.push(fragment);
    }

    // (3) Determine our "auto" block size.
    const autoBlockSize = maxChildBlockSize + edges.block;

    // (4) Return our fragment.
    return {
      autoBlockSize,
      childFragments,
    }
  }
});
```

The `layout` function is your callback into the browsers layout phase in the
rendering engine. You are given:
 - `children`, the list of children boxes you should perform layout upon.
 - `edges`, the size of *your* borders, scrollbar, and padding in the logical coordinate system.
 - `constraints`, the constraints which the fragment you produce should meet.
 - `style`, the _readonly_ style for the current layout.

Layout eventually will return a dictionary will what the resulting fragment of that layout should
be.

The above example would be used in CSS by:
```css
.centering {
  display: layout(centering);
}
```

### Step (1) - Determine our (inner) available size ###

The first thing that you'll probably want to do for most layouts is to determine your "inner" size.

The `constraints` object passed into the layout function pre-calculates your inline-size (width),
and potentially your block-size (height) if there is enough information to do so (e.g. the element
has `height: 100px` specified).

See [developer.mozilla.org](https://developer.mozilla.org) for an explanation of what
[width](https://developer.mozilla.org/en-US/docs/Web/CSS/width) and
[height](https://developer.mozilla.org/en-US/docs/Web/CSS/height), etc will resolve to.

The `edges` object represents the border, scrollbar, and padding of your element. In order to
determine our "inner" size we subtract the `edges.all` from our calculated sizes. For example:

```js
const availableInlineSize = constraints.fixedInlineSize - edges.inline;
const availableBlockSize = constraints.fixedBlockSize ?
    constraints.fixedBlockSize - edges.block :
    null;
```

We keep `availableBlockSize` null if `constraints.fixedBlockSize` wasn't able to be computed.

### Step (2) - Perform layout upon the child ###

Performing layout on a child can be done with the `layoutNextFragment` method. E.g.

```js
const fragment = await child.layoutNextFragment({
    availableInlineSize,
    availableBlockSize,
});
```

The first argument is the "constraints" which you are giving to the child. They can be:
 - `availableInlineSize` & `availableBlockSize` - A child fragment will try and "fit" within this
     given space.
 - `fixedInlineSize` & `fixedBlockSize` - A child fragment will be "forced" to be this size.
 - `percentageInlineSize` & `percentageBlockSize` - Percentages will be resolved against this size.

As layout may be paused or run on a different thread, the API is asynchronous.

The result of performing layout on a child is a `LayoutFragment`. A fragment is read-only except for
setting the offset relative to the parent fragment.

```js
fragment instanceof LayoutFragment; // true

// The resolved size of the fragment.
fragment.inlineSize;
fragment.blockSize;

// We can set the offset relative to the current layout.
fragment.inlineOffset = 10;
fragment.blockOffset = 20;
```

### Step (3) - Determine our "auto" block size ###

Now that we know how large our biggest child is going to be, we can calculate our "auto" block size.
This is the size the element will be if there are no other block-size constraints (e.g. `height:
100px`).

In this layout algorithm, we just add the `edges.block` size to the largest child we found:
```js
const autoBlockSize = maxChildBlockSize + edges.block;
```

### Step (4) - Return our fragment ###

Finally we return a dictionary which represents the fragment we wish the rendering engine to create
for us. E.g.
```js
const result = {
  autoBlockSize,
  childFragments,
};
```

The important things to note here are that you need to explicitly say which `childFragments` you
would like to render. If you give this an empty array you won't render any of your children.

Querying Style
--------------

While not present in the "centering" example, it is possible to query the style of the element you
are performing layout for, and all children. E.g.

```html
<!DOCTYPE html>
<style>
.parent { display: layout(style-read); --a-number: 42; }
.child { --a-string: hello; }
</style>
<div class="parent">
  <div class="child"></div>
</div>
```

```js
registerLayout('style-read', class {
  static inputProperties = ['--a-number'];
  static childInputProperties = ['--a-string'];

  async layout(children, edges, constraints, styleMap) {
    // We can read our own style:
    styleMap.get('--a-number').value === 42;

    // And our children:
    children[0].styleMap.get('--a-string').toString() === 'hello';
  }
});
```

You can use this to implement properties which your layout depends on, a similar thing that native
layouts use is `flex-grow` for flexbox, or `grid-template-areas` for grid.

Text Layout
-----------

By default layouts force all of their children to be blockified. This means for example if you have:
```html
<div class="layout">
  I am some text
  <div class="child"></div>
</div>
```

The engine will conceptually force the text `I am some text` to be surrounded by a `<div>`. E.g.
```html
<div class="layout">
  <div>I am some text</div>
  <div class="child"></div>
</div>
```

This is important as the above `centering` layout would have to deal with text _fragmentation_, a
few native layouts use this trick to simplify their algorithms, for example grid and flexbox.

### Text Fragmentation ###

In the above `centering` example, we forced each `LayoutChild` to produce exactly one
`LayoutFragment`.

We are able to ensure children do not blockify by setting the `childDisplay` to `normal`, e.g.
```js
registerLayout('example', class {
  static layoutOptions = {childDisplay: 'normal'};
});
```

Now a `LayoutChild` which represents some text is able to produce more than one `Fragment`. E.g.

```text
|---- Inline Available Size ----|
The quick brown fox jumped over the lazy dog.
```

```js
child instanceof LayoutChild;

const fragment1 = yield child.layoutNextFragment(constraints);
const fragment2 = yield child.layoutNextFragment(constraints, fragment1.breakToken);

fragment2.breakToken == null;
```

In the above example the text child produces two fragments. Containing:
1. `The quick brown fox jumped over`
2. `the lazy dog.`

The critical detail here to be aware of is the concept of a `BreakToken`. The `BreakToken` contains
all of the information necessary to continue/resume the layout where the child finished.

We pass the `BreakToken` to add back into the `layout()` call in order to produce the next fragment.

### A Basic Text Layout ###

```js
registerLayout('basic-inline', class {
  static layoutOptions = {childDisplay: 'normal'};

  async layout(children, edges, constraints, styleMap) {
    // Determine our (inner) available size.
    const availableInlineSize = constraints.fixedInlineSize - edges.inline;
    const availableBlockSize = constraints.fixedBlockSize !== null ?
        constraints.fixedBlockSize - edges.block : null;

    const constraints = {
      availableInlineSize,
      availableBlockSize,
    };

    const childFragments = [];

    let blockOffset = edges.blockStart;
    let child = children.shift();
    let childBreakToken = null;
    while (child) {
      // Layout the next line, the produced line will try and respect the
      // availableInlineSize given, you could use this to achieve a column
      // effect or similar.
      const fragment = await child.layoutNextFragment(constraints, childBreakToken);
      childFragments.push(fragment);

      // Position the fragment, note we coulld do something special here, like
      // placing all the lines on a "rythimic grid", or similar.
      fragment.inlineOffset = edges.inlineStart;
      fragment.blockOffset = blockOffset;

      blockOffset += fragment.blockSize;

      if (fragment.breakToken) {
        childBreakToken = fragment.breakToken;
      } else {
        // If a fragment doesn't have a break token, we move onto the next
        // child.
        child = children.shift();
        childBreakToken = null;
      }
    }

    // Determine our "auto" block size.
    const autoBlockSize = blockOffset + edges.blockEnd;

    // Return our fragment.
    return {
      autoBlockSize,
      childFragments,
    };
  }
});
```

The above example is slightly more complex than the previous centering layout because of the ability
for text children to fragment.

That said it has all the same steps as before:
 1. Resolving the (inner) available size.
 2. Performing layout and positioning children fragments.
 3. Resolving the "auto" block size.
 4. Returning the fragment.

Scrolling
---------

We have been handling scrolling in the above example but we haven't talked about it yet.

The `edges` object passed into `layout()` respects the `overflow` property.
For example if we are `overflow: hidden`, `edges` object won't include the scrollbar width.

For `overflow: auto` the engine will typically perform a layout without a scrollbar, then if it
detects overflow, with a scrollbar. As long as you respect the layout "edges" your layout algorithm
should work as expected.

Block Fragmentation
-------------------

Some native layouts on the web support what is known as block fragmentation. For example:

```html
<style>
.multicol {
  columns: 3;
}
</style>
<div class="multicol">
This is some text.
<table>
<!-- SNIP! -->
</table>
This is some more text.
</div>
```

In the above example the `multicol` div may produce three (3) fragments.
 1. `{fragment}This is some text.{/fragment}`
 2. `{fragment}{fragment type=table}{/fragment} This is{/fragment}`
 3. `{fragment}some more text.{/fragment}`

We can make our children fragment by passing them a constraint space with a fragmentation line. E.g.

```js
registerLayout('special-multi-col', class {
  async layout(children, edges, constraints, styleMap, breakToken) {
    for (let child of children) {
      // Create a constraint space with a fragmentation line.
      const childConstraints = {
        availableInlineSize,
        availableBlockSize,
        blockFragmentationOffset: availableBlockSize,
        blockFragmentationType: 'column',
      });

      const fragment = await child.layoutNextFragment(childConstraints);
    }

    // ... 
  }
});
```

In the above example each of the children will attempt to fragment in the block direction when they
exceed `blockFragmentationOffset`. The type is a `'column'` which will mean it works in conjunction
with rules like `break-inside: avoid-column`.

We can also allow our own layout to be fragmented by respecting the fragmentation line. E.g.

```js
registerLayout('basic-inline', class {
  async layout(children, edges, constraints, styleMap, breakToken) {

    // We can check if we need to fragment in the block direction.
    if (constraints.blockFragmentationType != 'none') {
      // We need to fragment!
    }

    // We can get the start child to start layout at with the breakToken. E.g.
    let child = null;
    let childToken = null;
    if (breakToken) {
      childToken = breakToken.childTokens[0]; // We can actually have multiple
                                              // children break. But for now
                                              // we'll just use one.
      child = childToken.child;
    } else {
      child = children[0];
    }

    // SNIP!

    return {
      autoBlockSize,
      childFragments,
      breakToken: {
        data: /* you can place arbitary data here */,
        childTokens: [childToken]
      }
    }
  }
});
```

The additional complexity here is that you need to create and receive your own break tokens.

Closing Words
-------------

This is a complex API and it uses foreign terminology. But we really want to give you, the web
developer, the power that the rendering engines have when it comes to layout. Enjoy! :)

