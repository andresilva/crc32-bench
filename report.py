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
        background="white",
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


def generate_html_table(group_name: str, crate_data: dict) -> str:
    """Generate an HTML table for benchmark results."""
    all_sizes = set()
    for crate_results in crate_data.values():
        all_sizes.update(crate_results.keys())
    sizes = sorted(all_sizes, key=size_to_bytes)

    rows = ["<table>", "<thead><tr><th>Crate</th>"]
    for size in sizes:
        rows.append(f"<th>{size}</th>")
    rows.append("</tr></thead><tbody>")

    for crate_name in sorted(crate_data.keys()):
        size_results = crate_data[crate_name]
        rows.append(f"<tr><td><strong>{crate_name}</strong></td>")
        for size in sizes:
            if size in size_results:
                size_bytes = size_to_bytes(size)
                throughput = calc_throughput_gibs(size_bytes, size_results[size])
                rows.append(f"<td>{throughput:.2f}</td>")
            else:
                rows.append("<td>-</td>")
        rows.append("</tr>")

    rows.append("</tbody></table>")
    return "\n".join(rows)


def generate_report(results: dict, output_dir: Path) -> None:
    """Generate markdown report (for GitHub README) and HTML report (for GitHub Pages)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Common header info
    crates_table_md = """| Crate | Description |
|-------|-------------|
| [`crc`](https://crates.io/crates/crc) | Generic CRC library (software, table-based) |
| [`crc-fast`](https://crates.io/crates/crc-fast) | SIMD-accelerated, supports all CRC variants |
| [`crc32fast`](https://crates.io/crates/crc32fast) | SIMD-accelerated CRC32 |
| [`crc32c`](https://crates.io/crates/crc32c) | Hardware-accelerated CRC32C (SSE4.2/ARM) |"""

    crates_table_html = """<table>
<thead><tr><th>Crate</th><th>Description</th></tr></thead>
<tbody>
<tr><td><a href="https://crates.io/crates/crc"><code>crc</code></a></td><td>Generic CRC library (software, table-based)</td></tr>
<tr><td><a href="https://crates.io/crates/crc-fast"><code>crc-fast</code></a></td><td>SIMD-accelerated, supports all CRC variants</td></tr>
<tr><td><a href="https://crates.io/crates/crc32fast"><code>crc32fast</code></a></td><td>SIMD-accelerated CRC32</td></tr>
<tr><td><a href="https://crates.io/crates/crc32c"><code>crc32c</code></a></td><td>Hardware-accelerated CRC32C (SSE4.2/ARM)</td></tr>
</tbody></table>"""

    # Markdown report (GitHub README - static images)
    md_lines = [
        "# CRC32 Benchmark Results",
        "",
        f"Generated: {timestamp}",
        "",
        "CPU: AMD Ryzen 9 9950X3D",
        "",
        "## Summary",
        "",
        "This report compares the throughput of various CRC32 implementations in Rust.",
        "",
        "### Crates Tested",
        "",
        crates_table_md,
        "",
    ]

    # HTML report (GitHub Pages - interactive SVGs)
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"UTF-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        "  <title>CRC32 Benchmark Results</title>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }",
        "    h1, h2, h3 { color: #333; }",
        "    table { border-collapse: collapse; margin: 20px 0; }",
        "    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: right; }",
        "    th { background: #f6f8fa; text-align: left; }",
        "    td:first-child { text-align: left; }",
        "    object { display: block; max-width: 100%; margin: 20px 0; }",
        "    a { color: #0366d6; }",
        "    code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>CRC32 Benchmark Results</h1>",
        f"  <p>Generated: {timestamp}</p>",
        "  <p>CPU: AMD Ryzen 9 9950X3D</p>",
        "  <h2>Summary</h2>",
        "  <p>This report compares the throughput of various CRC32 implementations in Rust.</p>",
        "  <h3>Crates Tested</h3>",
        f"  {crates_table_html}",
    ]

    for group_name in sorted(results.keys()):
        crate_data = results[group_name]
        if not crate_data:
            continue

        svg_filename = f"{group_name.lower().replace('-', '_')}.svg"
        svg_path = output_dir / svg_filename

        generate_svg_plot(group_name, crate_data, svg_path)

        # Markdown: static image
        md_lines.extend([
            f"## {group_name}",
            "",
            f"![{group_name} Throughput]({svg_filename})",
            "",
            "### Throughput (GiB/s)",
            "",
            generate_markdown_table(group_name, crate_data),
            "",
        ])

        # HTML: interactive object
        html_lines.extend([
            f"  <h2>{group_name}</h2>",
            f'  <object type="image/svg+xml" data="{svg_filename}">{group_name} Throughput</object>',
            "  <h3>Throughput (GiB/s)</h3>",
            f"  {generate_html_table(group_name, crate_data)}",
        ])

    md_lines.append("")
    html_lines.extend(["</body>", "</html>"])

    # Write markdown
    md_path = output_dir / "BENCHMARKS.md"
    md_path.write_text("\n".join(md_lines))
    print(f"Generated: {md_path}")

    # Write HTML
    html_path = output_dir / "index.html"
    html_path.write_text("\n".join(html_lines))
    print(f"Generated: {html_path}")


def main():
    criterion_path = Path("target/criterion")

    if not criterion_path.exists():
        print(f"Error: {criterion_path} not found. Run 'cargo bench' first.")
        return

    results = parse_criterion_results(criterion_path)

    output_dir = Path("report")
    output_dir.mkdir(exist_ok=True)

    generate_report(results, output_dir)

    print(f"\nReports saved to {output_dir}/")
    print(f"  - BENCHMARKS.md (GitHub README)")
    print(f"  - index.html (GitHub Pages, interactive)")


if __name__ == "__main__":
    main()
