use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use rand::{rngs::StdRng, Rng, SeedableRng};
use std::hint::black_box;

const SIZES: &[(usize, &str)] = &[
    (64, "64B"),
    (256, "256B"),
    (512, "512B"),
    (1024, "1KB"),
    (2 * 1024, "2KB"),
    (4 * 1024, "4KB"),
    (16 * 1024, "16KB"),
    (64 * 1024, "64KB"),
    (512 * 1024, "512KB"),
    (1024 * 1024, "1MB"),
    (4 * 1024 * 1024, "4MB"),
];

fn generate_data(size: usize) -> Vec<u8> {
    let mut rng = StdRng::seed_from_u64(0xDEADBEEF);
    let mut data = vec![0u8; size];
    rng.fill(&mut data[..]);
    data
}

fn bench_crc32(c: &mut Criterion) {
    let mut group = c.benchmark_group("CRC32");

    for &(size, name) in SIZES {
        let data = generate_data(size);
        group.throughput(Throughput::Bytes(size as u64));

        // crc32fast
        group.bench_with_input(BenchmarkId::new("crc32fast", name), &data, |b, data| {
            b.iter(|| crc32fast::hash(black_box(data)))
        });

        // crc-fast
        group.bench_with_input(BenchmarkId::new("crc-fast", name), &data, |b, data| {
            b.iter(|| crc_fast::checksum(crc_fast::CrcAlgorithm::Crc32IsoHdlc, black_box(data)))
        });

        // crc (generic, table-based baseline)
        group.bench_with_input(BenchmarkId::new("crc", name), &data, |b, data| {
            const CRC32_ISO: crc::Crc<u32> = crc::Crc::<u32>::new(&crc::CRC_32_ISO_HDLC);
            b.iter(|| CRC32_ISO.checksum(black_box(data)))
        });
    }

    group.finish();
}

fn bench_crc32c(c: &mut Criterion) {
    let mut group = c.benchmark_group("CRC32C");

    for &(size, name) in SIZES {
        let data = generate_data(size);
        group.throughput(Throughput::Bytes(size as u64));

        // crc32c
        group.bench_with_input(BenchmarkId::new("crc32c", name), &data, |b, data| {
            b.iter(|| crc32c::crc32c(black_box(data)))
        });

        // crc-fast
        group.bench_with_input(BenchmarkId::new("crc-fast", name), &data, |b, data| {
            b.iter(|| crc_fast::checksum(crc_fast::CrcAlgorithm::Crc32Iscsi, black_box(data)))
        });

        // crc (generic, table-based baseline)
        group.bench_with_input(BenchmarkId::new("crc", name), &data, |b, data| {
            const CRC32C: crc::Crc<u32> = crc::Crc::<u32>::new(&crc::CRC_32_ISCSI);
            b.iter(|| CRC32C.checksum(black_box(data)))
        });
    }

    group.finish();
}

criterion_group!(benches, bench_crc32, bench_crc32c);
criterion_main!(benches);
