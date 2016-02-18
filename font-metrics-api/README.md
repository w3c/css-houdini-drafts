Font Metrics API
================

# Motivation

Box tree/view object stuff will be great as an underpinning for custom layout, particularly when it's extended to cover line boxes. But the proposals discussed so far lack some information that's needed for layout that depends on font metrics. It's not sufficient to know where the line box is being laid out. You also need to know where the glyphs inside that line box are being drawn.

There are also some parts of layout that are typographically-intensive, like line breaking. Allowing script to substitute its own line breaking would be an excellent extensibility point that's often asked for.

# Examples:

The align-items:baseline feature in flex layout
* needs to know where the first baseline of each flex item lands

Initial letter
* needs baseline and cap height from the initial letter, and a baseline measurement for the in-flow content

Baseline grid
* needs a baseline for each line box in the element

Math layout
* needs much much more than the above, including individual glyph advances and bounds.

Line breaking
* needs access to font data, all of the style inputs for text, and layout information (available line lengths, intrusions like floats, etc.)

# Font data versus typographic measurement

I (Alan) initially thought that exposing the actual font data could be a good first step, but conversations I've had have convinced me that there's a better stepping-stone to use. Given raw font metrics, one has to reverse-engineer how the browser will use those metrics in order to determine where baselines, etc. will actually be drawn. Direct access to all of the font information was not sufficient for dropcap.js, because browsers use the font information in slightly different ways - we still had to sample the rendered text in each browser to determine where glyphs were placed.

Instead, we could expose how these font metrics are used by the browser, giving access to typographic layout results. If and when we have view objects it will make sense to make these results available at several levels - down to the glyph level (for advances, bounds, etc.), for runs of text within a line box (aggregating some glyph information and/or pulling information from the first glyph), for line boxes (aggregating and/or first run information), for fragments (aggregating and/or first line box) and for elements (aggregating and/or first fragment). So even without the underlying view objects it may make sense to start with attributes on higher-level objects, informed by the underlying layout structure. For example, a possible 'firstBaselinePosition' attribute of an Element might give a pixel measurement for the baseline of the first glyph of the first line box of the first fragment, measured from the top of the fragment.

There's another argument that people want direct access to font data to enable their own text layout routines to draw on a canvas or invoke in a custom paint routine. That's a fine use case, but I think it's probably a lower priority than allowing measurement of text laid out by the browser. Math layout will require actual font data, but how that data is used will depend on the layout measures above. So we should eventually get to the point of exposing raw font data, but either after or at the same time as exposing at least some of the layout results.

There is also an argument that exposing information on higher-level constructs can result in a dead-end, since the underlying complexities of font selection, shaping, line-breaking, et.al. might not be taken into account in either aggregating or choosing what to sample for something as high-level as an element (or even a line box). That's certainly a risk, but if that risk is considered I think it will be possible to come up with a small set of useful high-level APIs without having to wait for agreement on how to standardize lower-level text layout constructs.

# Four kinds of Font Data

We discussed four different areas that seemed to qualify as 'font metrics' during the F2F in Sydney, in January 2016. These are:

1. What font(s) are being used? This is complicated because multiple fonts can be used per paragraph, per line,
   per word, and even per glyph. The fonts should be exposed in the form of handles with complete font information, and
   (for web fonts) a handle to the raw font data. dbaron & eae are going to own this area and propose an API.

1. Browsers make use of some font information for layout (including multiple different baselines). In order to do this,
   sometimes baseline information must be synthesized from the available data. However, this information is a small
   subset of all possible data that could conceivably be synthesized about fonts. Area 2 pertains solely to information
   that is already available in fonts, or that must be synthesized by browsers in order to successfully layout text.
   This information should be exposed by browsers on a font-by-font basis. stevez & astearns are going to own this
   area and propose an API.

1. Fonts carry more metrics than browsers use. Often these metrics are buggy or incorrect. Nevertheless, access to the
   raw metrics is useful. While we recognize that this is an area of interest, we decided to defer work on this for now,
   given that the raw data is already going to be accessible via area 1, and that there are existing JS parsers for multiple
   kinds of font.

1. Font geometry and metrics that browsers don't already used could conceivably be synthesized by browsers. However, in order
   to do so, we'd need to standardize the algorithms used to perform these syntheses. As a result, we decided to defer working
   on this area for now.
