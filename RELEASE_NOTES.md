# Release Notes - v2.0.0

Welcome to the production-quality public release of **AVI Core** (v2.0.0)! 

This major version release hardens the core CLI toolkit and Windows Explorer context menu integration into a robust, high-performance, and resource-conscious platform.

## Highlights & New Features

* **Intelligent Parallel Batch Processing**: Multi-file batch queues are now processed concurrently using dynamic worker scheduling that throttles workload dynamically based on CPU cores and physical memory load.
* **Stream Integrity & Parity Verification**: Every conversion undergoes a strict two-phase atomic commit verifying output readability, track availability, and duration parity within a 2-second tolerance.
* **Auto-GPU Fallback Chain**: Intelligent encoder selection detects and selects the fastest available hardware encoding path (`NVENC` ➔ `QSV` ➔ `AMF` ➔ `CPU`) on the fly.
* **Container-Aware Metadata Mapping**: Preserves EXIF tags, color maps, ICC profiles, audio downmix tables, and stream headers according to the capabilities of the target container.
* **Production-Grade Audit & Cleanup**: Removed all leftover binary artifacts from root, configured Git exclusions, resolved CLI command annotations, and implemented a robust test suite covering core features.
