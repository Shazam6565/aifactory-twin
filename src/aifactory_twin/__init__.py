"""A SimReady OpenUSD asset pipeline and validation harness for AI factory digital twins.

Layout:
    ingest/    source -> normalized USD (units, naming, xforms, provenance)
    author/    layer authoring (simready, domain layers, scene assembly)
    optimize/  instancing strategies
    validate/  usd validation + custom SimReady rules -> report
    consume/   ovrtx render, ovphysx physics  (Linux + NVIDIA GPU only)
"""

__version__ = "0.1.0"
