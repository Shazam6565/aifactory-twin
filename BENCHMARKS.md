# Benchmarks

Method first, numbers second. A table without a stated method is not a benchmark.

> **Status: method fixed, numbers unpopulated.** Deliverable 4 in `SCOPE.md` is not built, so
> there is nothing to measure yet. The table below is deliberately empty rather than estimated.

---

## What is measured

**Measured:** stage-open wall time, and composed prim count.

**Not measured: VRAM, frame time, render throughput.** These require a GPU. They are **excluded
deliberately rather than estimated** — this repo publishes no number it has not measured. If
GPU numbers are ever wanted they belong in a separate table with its own stated hardware, not
interpolated into this one.

Measuring on CPU with `usd-core` alone is a choice, not a limitation: it makes every number here
reproducible on any laptop, with no GPU, no driver version, and no shader cache to warm.

## Method

- **Three runs** per configuration.
- **Median** reported. Not mean — a single slow first run should not move the number.
- **Cold process each time.** A fresh Python interpreter per run, so no stage cache, no
  resolver cache, and no import cost is carried between runs.
- Stage-open time is wall time around `Usd.Stage.Open`, excluding interpreter startup.
- Composed prim count is `len(list(stage.Traverse()))` after open.

## Environment

Recorded so someone else can tell whether their numbers should match.

| | |
|---|---|
| CPU | Apple M3 Pro, 11 cores |
| OS | macOS 26.5.2 (arm64) |
| Python | 3.12.11 |
| `usd-core` | 26.8 (pinned in `pyproject.toml`) |
| GPU | not used |

---

## Results

N = 512 unless stated.

| Config | Stage open (s) | Composed prims |
|---|---|---|
| Flattened, N=512 | | |
| + geometry as payload | | |
| + scenegraph instancing (racks) | | |
| + PointInstancer (floor tiles) | | |

Each row is cumulative: it adds one change to the row above it, so the difference between two
adjacent rows is the cost or saving of that one decision.

---

## What these numbers will and will not show

**Will show:** the effect of the composition decisions in `ARCHITECTURE.md` — what payloading
geometry saves at stage-open, and what instancing does to composed prim count.

**Will not show:** anything about rendering or simulation performance. A low prim count does not
mean a scene renders quickly. That claim needs `ovrtx` and a GPU, and it is not made here.
