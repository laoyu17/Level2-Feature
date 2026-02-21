# l2-features (English Summary)

[![CI](https://github.com/laoyu17/Level2-Feature/actions/workflows/ci.yml/badge.svg)](https://github.com/laoyu17/Level2-Feature/actions/workflows/ci.yml)

`l2-features` is an open-source toolkit for extracting microstructure features from Level2/Tick data.

## Highlights

- High-throughput batch pipeline with Polars/Arrow
- Incremental stream updater for online feature generation
- PyQt6 replay UI for interactive data playback and inspection
- Production-style engineering setup (CLI + CI + regression tests + docs)

## Demo

![l2-features demo replay](assets/demo_replay.gif)

## Quick Start

```bash
python -m pip install -e .
l2f validate-schema --input examples/sample_data/l2_sample.csv
l2f compute --input examples/sample_data/l2_sample.csv --output outputs/features.parquet
l2f benchmark --input examples/sample_data/l2_sample.csv --rows 200000 --mode both
```

- Schema note: L2+ depth levels must be complete per level (`bid_px_i/bid_sz_i/ask_px_i/ask_sz_i`) and contiguous.
- `trade_sign` uses `side` first (`-1/0/1`, `B/S`, `BUY/SELL`), then falls back to price movement when side is invalid.

For UI:

```bash
python -m pip install -e .[ui]
l2f ui
```

The UI supports both `batch-playback` and `stream-playback` modes.

## Repository

- GitHub: `https://github.com/laoyu17/Level2-Feature.git`
