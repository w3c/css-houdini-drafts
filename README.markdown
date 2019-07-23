### [CSS-TAG Houdini Task Force](https://wiki.css-houdini.org/) Specifications

This is the repository containing the [CSS/TAG Houdini Task Force specifications](https://drafts.css-houdini.org/).

In addition to this git repository, a Mercurial mirror is maintained at `https://hg.css-houdini.org/drafts`, if for whatever reason you prefer Mercurial.

Specification issues are raised and discussed in GitHub Issues in this repository.

We also maintain the [public-houdini mailing list](http://lists.w3.org/Archives/Public/public-houdini/) for general-interest topics.

New specifications are generally first incubated in the WICG, in particular:
- [Animation Worklet](https://github.com/WICG/animation-worklet)

# Tests

For normative changes, a corresponding
[web-platform-tests](https://github.com/web-platform-tests/wpt) PR is highly appreciated. Typically,
both PRs will be merged at the same time. Note that a test change that contradicts the spec should
not be merged before the corresponding spec change. If testing is not practical, please explain why
and if appropriate [file an issue](https://github.com/web-platform-tests/wpt/issues/new) to follow
up later. Add the `type:untestable` or `type:missing-coverage` label as appropriate.

