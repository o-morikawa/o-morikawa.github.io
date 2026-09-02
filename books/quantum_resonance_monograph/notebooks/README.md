# Computational companion

`resummation_workflow.wl` is the text-readable Wolfram Language companion to
the resummation appendix. It implements the zero-dimensional quartic
benchmark without requiring a notebook front end.

The method comparison is based on the public MIT-licensed repository
[`o-morikawa/Resummation`](https://github.com/o-morikawa/Resummation), inspected
at commit `11a9b71b8038c82080d31b803a40129921235934`. The monograph contains a
fresh compact implementation so that the calculation, conventions, and
failure checks agree with the printed appendix.

Before evaluating a Borel--Padé Laplace integral, inspect `borelPoles[order]`.
A pole on the positive integration axis requires a stated lateral or
principal-value prescription.
