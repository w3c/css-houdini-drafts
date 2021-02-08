# CSS Typed OM Explained

CSS Typed OM is an extensible API for the CSSOM that reduces the burden of manipulating a CSS property's value via string manipulation. It does so by exposing CSS values as typed JavaScript objects rather than strings.

## Motivation

The benefits of CSS Typed OM include:
* Allows the performant manipulation of values assigned to CSS properties. 
* Being able to write more maintainable code:
	* Your code is easier to understand,
	* Easier to write more generic code.

### Examples

### Getting a property's value

In CSSOM land:
We get specified and computed values for CSS properties of an element in CSSOM via the `.style` attribute on an element and the `getComputedStyle()` object respectively. 

In Typed OM:
We get them of `StylePropertyMaps` on elements. 

To get the specified height from an element we would use the following JS:
```
element.attributeStyleMap.get('height'); // returns a CSSUnitValue
```

Similarly to get the computed value of a CSS property we would do the following: 
```
element.computedStyleMap().get('height'); // returns a CSSUnitValue
```

### Changing a property's value

To understand the power of Typed OM take a look at the example in CSSOM below:

```
let heightValue = target.style.height.slice(0,-2);
heightValue++;
target.style.height = heightValue + 'px';
```

In the above example, we are manipulating the `height` CSS property by:
* extract the numeric portion of a string,
* performing mathematical operation,
* converting a number to a string,
* appending a unit to the resulting string.

The CSS parser will then parse the final string and convert it back to a number for the CSS engine. 

With Typed OM you can manipulate typed Javascript objects thereby eliminating the CSS Parser altogether. The above example will now read as follows:

```
let heightValue = element.attributeStyleMap.get('height');
heightValue.value++;
target.attributeStyleMap.set('height', heightValue);
```

In the above code, `heightValue` gets assigned a `CSSUnitValue` with a value set to the current value of the height and the unit set to 'px'. You can then modify the unit as you would do an integer and not have to incur the cost of manipulating a string.

## Spec references

### What is a CSSStyleValue?

[CSSStyleValue](https://drafts.css-houdini.org/css-typed-om-1/#cssstylevalue) is the base class through which all CSS values are expressed. For a detailed list of what CSSStyleValue subclasses each CSS property maps to please see [here](PLACEHOLDER). Values that aren't supported yet will also be considered as CSSStyleValue objects.

### What are the different CSSStyleValue subclasses?

#### CSSKeywordValue

[CSSKeywordValue](https://drafts.css-houdini.org/css-typed-om-1/#csskeywordvalue) objects represent CSS keywords and other identifiers. An example would be:

```
element.attributeStyleMap.set("display", new CSSKeywordValue("none")));
```

#### CSSNumericValue

[CSSNumericValue](https://drafts.css-houdini.org/css-typed-om-1/#cssnumericvalue) objects represent CSS values that are numeric in nature. 

The class can be broken down into two subclasses: 
* CSSUnitValues represent simple numbers with units - `CSSUnitValue(10, 'px')` for example is the typed representation of `10px`
* CSSMathValues represent more complex expressions - `CSSMathSum(CSS.em(1), CSS.px(5))` for example is the typed representation of `calc(1em + 5px)`

#### CSSTransformValue

[CSSTransformValue](https://drafts.css-houdini.org/css-typed-om-1/#csstransformvalue) objects represent via [CSSTransformComponents](https://drafts.css-houdini.org/css-typed-om-1/#csstransformcomponent) values, the different functions used by the `transform` property. 

#### CSSResourceValue

[CSSResourceValue](https://drafts.css-houdini.org/css-typed-om-1/#resourcevalue-objects) objects represent CSS values that require an asynchronous network fetch. Hence, they also describe the status the resource is in. Properties with image values (e.g. `background-image`), are represented by [CSSImageValues](https://drafts.css-houdini.org/css-typed-om-1/#cssimagevalue)

#### CSSColorValue

[CSSColorValue](https://drafts.css-houdini.org/css-typed-om-1/#colorvalue-objects) objects represent color values.

### What about Custom Properties?

Unregistered custom properties are represented by [CSSUnparsedValues](https://drafts.css-houdini.org/css-typed-om-1/#cssunparsedvalue) in the Typed OM API. `var()` references are represented using [CSSVariableReferenceValues](https://drafts.css-houdini.org/css-typed-om-1/#cssvariablereferencevalue).

## Future Capabilities

The current specification doesn't have support for the following, however support for the following is under consideration for Typed OM Level 2:

* URLs (that aren't images),
* Shapes, 
* Strings, 
* Counters, 
* etc.

## Go ahead - try it!

Currently you can try out CSS Typed OM in Chromium based browsers (it is behind a flag though.)

Do let us know if you are having trouble with Typed OM or are missing capabilities by filing an issue on [GitHub](https://github.com/w3c/css-houdini-drafts/issues/new).
