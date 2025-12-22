#[cfg(test)]
mod tests {
    use rand::{rngs::StdRng, Rng, SeedableRng};

    fn generate_data(size: usize) -> Vec<u8> {
        let mut rng = StdRng::seed_from_u64(0xDEADBEEF);
        let mut data = vec![0u8; size];
        rng.fill(&mut data[..]);
        data
    }

    #[test]
    fn crc32_implementations_match() {
        for size in [64, 256, 512, 1024, 4 * 1024, 512 * 1024, 1024 * 1024] {
            let data = generate_data(size);

            let crc32fast_result = crc32fast::hash(&data);
            let crc_fast_result =
                crc_fast::checksum(crc_fast::CrcAlgorithm::Crc32IsoHdlc, &data) as u32;
            let crc_result = crc::Crc::<u32>::new(&crc::CRC_32_ISO_HDLC).checksum(&data);

            assert_eq!(crc32fast_result, crc_fast_result);
            assert_eq!(crc32fast_result, crc_result);
        }
    }

    #[test]
    fn crc32c_implementations_match() {
        for size in [64, 256, 512, 1024, 4 * 1024, 512 * 1024, 1024 * 1024] {
            let data = generate_data(size);

            let crc32c_result = crc32c::crc32c(&data);
            let crc_fast_result =
                crc_fast::checksum(crc_fast::CrcAlgorithm::Crc32Iscsi, &data) as u32;
            let crc_result = crc::Crc::<u32>::new(&crc::CRC_32_ISCSI).checksum(&data);

            assert_eq!(crc32c_result, crc_fast_result);
            assert_eq!(crc32c_result, crc_result);
        }
    }
}
