Font Metrics API
================

# Motivation

Box tree/view object stuff will be great as an underpinning for custom layout, particularly when it's extended to cover line boxes. But the proposals discussed so far lack some information that's needed for layout that depends on font metrics. It's not sufficient to know where the line box is being laid out. You also need to know where the glyphs inside that line box are being drawn.

# Examples:

The align-items:baseline feature in flex layout
* needs to know where the first baseline of each flex item lands

Initial letter
* needs baseline and cap height from the initial letter, and a baseline measurement for the in-flow content

Baseline grid
* needs a baseline for each line box in the element

Math layout
* needs much much more than the above, including individual glyph advances and bounds.

# Font data versus layout results

I (Alan) initially thought that exposing the actual font data could be a good first step, but conversations I've had have convinced me that there's a better stepping-stone to use. Given raw font metrics, one has to reverse-engineer how the browser will use those metrics in order to determine where baselines, etc. will actually be drawn. Direct access to all of the font information was not sufficient for dropcap.js, because browsers use the font information in slightly different ways - we still had to sample the rendered text in each browser to determine where glyphs were placed.

Instead, we could expose how these font metrics are used by the browser, giving access to typographic layout results. If and when we have view objects it will make sense to make these results available at several levels - down to the glyph level (for advances, bounds, etc.), for runs of text within a line box (aggregating some glyph information and/or pulling information from the first glyph), for line boxes (aggregating and/or first run information), for fragments (aggregating and/or first line box) and for elements (aggregating and/or first fragment). So even without the underlying view objects it may make sense to start with attributes on higher-level objects, informed by the underlying layout structure. For example, a possible 'firstBaselinePosition' attribute of an Element might give a pixel measurement for the baseline of the first glyph of the first line box of the first fragment, measured from the top of the fragment.

There's another argument that people want direct access to font data to enable their own text layout routines to draw on a canvas or invoke in a custom paint routine. That's a fine use case, but I think it's probably a lower priority than allowing measurement of text laid out by the browser. Math layout will require actual font data, but how that data is used will depend on the layout measures above. So we should eventually get to the point of exposing raw font data, but either after or at the same time as exposing at least some of the layout results.

There is also an argument that exposing information on higher-level constructs can result in a dead-end, since the underlying complexities of font selection, shaping, line-breaking, et.al. might not be taken into account in either aggregating or choosing what to sample for something as high-level as an element (or even a line box). That's certainly a risk, but if that risk is considered I think it will be possible to come up with a small set of useful high-level APIs without having to wait for agreement on how to standardize lower-level text layout constructs.