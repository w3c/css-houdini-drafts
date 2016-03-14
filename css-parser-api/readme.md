CSS Parser Explainer
==============================

The CSS Parser API goal is to solve common use cases
that web developers encounter where they want to parse
a string that follows the syntax and grammar of CSS and
utilize the browser's built in parser to return an object.

Current Use Cases
------------------
* Be able to pass the following in to the parser and get
a representative object in return
    * property and value
    * selector (see [bug 24115](https://www.w3.org/Bugs/Public/show_bug.cgi?id=24115))
    * css rule
    * full stylesheet
* Be able to turn off/on error handling which will enable
the capability to use the parser for custom language needs
or CSS polyfilling.
