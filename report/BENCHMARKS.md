# CRC32 Benchmark Results

Generated: 2025-12-22 12:16:29

CPU: AMD Ryzen 9 9950X3D

## Summary

This report compares the throughput of various CRC32 implementations in Rust.

### Crates Tested

| Crate | Description |
|-------|-------------|
| [`crc`](https://crates.io/crates/crc) | Generic CRC library (software, table-based) |
| [`crc-fast`](https://crates.io/crates/crc-fast) | SIMD-accelerated, supports all CRC variants |
| [`crc32fast`](https://crates.io/crates/crc32fast) | SIMD-accelerated CRC32 |
| [`crc32c`](https://crates.io/crates/crc32c) | Hardware-accelerated CRC32C (SSE4.2/ARM) |

## CRC32

<object type="image/svg+xml" data="crc32.svg">CRC32 Throughput</object>

### Throughput (GiB/s)

| Crate | 64B | 256B | 512B | 1KB | 2KB | 4KB | 16KB | 64KB | 512KB | 1MB | 4MB |
|-------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| **crc** | 0.87 | 0.69 | 0.66 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 |
| **crc-fast** | 2.38 | 11.27 | 19.41 | 36.08 | 56.96 | 67.36 | 78.02 | 80.51 | 81.97 | 81.28 | 80.08 |
| **crc32fast** | 6.87 | 18.33 | 19.36 | 20.01 | 20.32 | 20.48 | 20.45 | 20.60 | 20.58 | 20.62 | 20.52 |

## CRC32C

<object type="image/svg+xml" data="crc32c.svg">CRC32C Throughput</object>

### Throughput (GiB/s)

| Crate | 64B | 256B | 512B | 1KB | 2KB | 4KB | 16KB | 64KB | 512KB | 1MB | 4MB |
|-------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| **crc** | 0.87 | 0.69 | 0.67 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | 0.64 |
| **crc-fast** | 12.13 | 29.22 | 49.24 | 63.09 | 73.31 | 80.60 | 82.10 | 81.74 | 82.40 | 81.40 | 80.14 |
| **crc32c** | 6.64 | 8.90 | 8.94 | 9.11 | 9.14 | 9.44 | 9.61 | 10.11 | 10.28 | 10.25 | 10.02 |

