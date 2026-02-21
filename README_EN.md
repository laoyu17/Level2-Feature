# l2-features (English Summary)

`l2-features` is an open-source toolkit for extracting microstructure features from Level2/Tick data.

## Highlights

- High-throughput batch pipeline with Polars/Arrow
- Incremental stream updater for online feature generation
- PyQt6 replay UI for interview/demo scenarios
- Production-style engineering setup (CLI + CI + regression tests + docs)

## Quick Start

```bash
python -m pip install -e .
l2f validate-schema --input examples/sample_data/l2_sample.csv
l2f compute --input examples/sample_data/l2_sample.csv --output outputs/features.parquet
l2f benchmark --input examples/sample_data/l2_sample.csv --rows 200000 --mode both
```

For UI:

```bash
python -m pip install -e .[ui]
l2f ui
```

## Repository

- GitHub: `https://github.com/laoyu17/Level2-Feature.git`
