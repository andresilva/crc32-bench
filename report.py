#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pygal",
# ]
# ///

import json
import re
from datetime import datetime
from pathlib import Path

import pygal
from pygal.style import CleanStyle


def is_size_dir(name: str) -> bool:
    """Check if directory name looks like a size label (64B, 1KB, 1MB, etc.)."""
    return bool(re.match(r"^\d+[BKGM]B?$", name))


def parse_criterion_results(base_path: Path) -> dict:
    """Parse Criterion benchmark results from JSON files."""
    results = {}

    for group_dir in base_path.iterdir():
        if not group_dir.is_dir() or group_dir.name == "report":
            continue

        group_name = group_dir.name
        results[group_name] = {}

        for crate_dir in group_dir.iterdir():
            if not crate_dir.is_dir():
                continue

            crate_name = crate_dir.name
            if is_size_dir(crate_name) or crate_name == "report":
                continue

            results[group_name][crate_name] = {}

            for size_dir in crate_dir.iterdir():
                if not size_dir.is_dir() or size_dir.name == "report":
                    continue

                size_name = size_dir.name
                estimates_file = size_dir / "new" / "estimates.json"

                if estimates_file.exists():
                    with open(estimates_file) as f:
                        data = json.load(f)
                        mean_ns = data["mean"]["point_estimate"]
                        results[group_name][crate_name][size_name] = mean_ns

    return results


def size_to_bytes(size_str: str) -> int:
    """Convert size string like '64B', '1KB', '1MB' to bytes."""
    size_str = size_str.strip()
    if size_str.endswith("MB"):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith("KB"):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith("B"):
        return int(size_str[:-1])
    return int(size_str)


def calc_throughput_gibs(size_bytes: int, time_ns: float) -> float:
    """Calculate throughput in GiB/s."""
    seconds = time_ns / 1e9
    bytes_per_sec = size_bytes / seconds
    return bytes_per_sec / (1024**3)


def generate_svg_plot(group_name: str, crate_data: dict, output_path: Path) -> None:
    """Generate an SVG plot for a benchmark group."""
    all_sizes = set()
    for crate_results in crate_data.values():
        all_sizes.update(crate_results.keys())
    sizes = sorted(all_sizes, key=size_to_bytes)

    style = CleanStyle
    chart = pygal.Line(
        style=style,
        title=f"{group_name} Throughput Comparison",
        x_title="Data Size",
        y_title="Throughput (GiB/s)",
        legend_at_bottom=True,
        show_dots=True,
        dots_size=4,
        stroke_style={"width": 2},
        width=900,
        height=500,
        explicit_size=True,
    )
    chart.x_labels = sizes

    for crate_name in sorted(crate_data.keys()):
        size_results = crate_data[crate_name]
        throughputs = []
        for size in sizes:
            if size in size_results:
                size_bytes = size_to_bytes(size)
                throughput = calc_throughput_gibs(size_bytes, size_results[size])
                throughputs.append(round(throughput, 2))
            else:
                throughputs.append(None)
        chart.add(crate_name, throughputs)

    chart.render_to_file(str(output_path))
    print(f"Generated: {output_path}")


def generate_markdown_table(group_name: str, crate_data: dict) -> str:
    """Generate a markdown table for benchmark results."""
    all_sizes = set()
    for crate_results in crate_data.values():
        all_sizes.update(crate_results.keys())
    sizes = sorted(all_sizes, key=size_to_bytes)

    # Header
    header = "| Crate | " + " | ".join(sizes) + " |"
    separator = "|-------|" + "|".join(["-------:" for _ in sizes]) + "|"

    rows = []
    for crate_name in sorted(crate_data.keys()):
        size_results = crate_data[crate_name]
        row_values = [f"**{crate_name}**"]
        for size in sizes:
            if size in size_results:
                size_bytes = size_to_bytes(size)
                throughput = calc_throughput_gibs(size_bytes, size_results[size])
                row_values.append(f"{throughput:.2f}")
            else:
                row_values.append("-")
        rows.append("| " + " | ".join(row_values) + " |")

    return "\n".join([header, separator] + rows)


def generate_report(results: dict, output_dir: Path) -> None:
    """Generate the full markdown report."""
    report_lines = [
        "# CRC32 Benchmark Results",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "This report compares the throughput of various CRC32 implementations in Rust.",
        "",
        "### Crates Tested",
        "",
        "| Crate | Description |",
        "|-------|-------------|",
        "| `crc` | Generic CRC library (software, table-based) |",
        "| `crc-fast` | SIMD-accelerated, supports all CRC variants |",
        "| `crc32fast` | SIMD-accelerated CRC32 |",
        "| `crc32c` | Hardware-accelerated CRC32C (SSE4.2/ARM) |",
        "",
    ]

    for group_name in sorted(results.keys()):
        crate_data = results[group_name]
        if not crate_data:
            continue

        svg_filename = f"{group_name.lower().replace('-', '_')}.svg"
        svg_path = output_dir / svg_filename

        generate_svg_plot(group_name, crate_data, svg_path)

        report_lines.extend([
            f"## {group_name}",
            "",
            f"![{group_name} Throughput]({svg_filename})",
            "",
            "### Throughput (GiB/s)",
            "",
            generate_markdown_table(group_name, crate_data),
            "",
        ])

    # Find the fastest for each category
    report_lines.extend([
        "## Conclusions",
        "",
    ])

    for group_name in sorted(results.keys()):
        crate_data = results[group_name]
        if not crate_data:
            continue

        # Find best performer at largest size
        all_sizes = set()
        for crate_results in crate_data.values():
            all_sizes.update(crate_results.keys())
        largest_size = max(all_sizes, key=size_to_bytes)
        largest_bytes = size_to_bytes(largest_size)

        best_crate = None
        best_throughput = 0
        for crate_name, size_results in crate_data.items():
            if largest_size in size_results:
                throughput = calc_throughput_gibs(largest_bytes, size_results[largest_size])
                if throughput > best_throughput:
                    best_throughput = throughput
                    best_crate = crate_name

        if best_crate:
            report_lines.append(
                f"- **{group_name}**: `{best_crate}` is fastest at {largest_size} "
                f"with {best_throughput:.2f} GiB/s"
            )

    report_lines.append("")

    report_path = output_dir / "BENCHMARKS.md"
    report_path.write_text("\n".join(report_lines))
    print(f"Generated: {report_path}")


def main():
    criterion_path = Path("target/criterion")

    if not criterion_path.exists():
        print(f"Error: {criterion_path} not found. Run 'cargo bench' first.")
        return

    results = parse_criterion_results(criterion_path)

    output_dir = Path("report")
    output_dir.mkdir(exist_ok=True)

    generate_report(results, output_dir)

    print(f"\nReport saved to {output_dir}/BENCHMARKS.md")


if __name__ == "__main__":
    main()
