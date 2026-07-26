#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuleMapping:
    """A source-file collection and its generated target file."""

    sources: tuple[str, ...]
    target: str


RULE_TYPE_MAPPING: dict[str, str] = {
    "DOMAIN": "HOST",
    "DOMAIN-SUFFIX": "HOST-SUFFIX",
    "DOMAIN-KEYWORD": "HOST-KEYWORD",
    "DOMAIN-WILDCARD": "HOST-WILDCARD",
    "IP-CIDR": "IP-CIDR",
    "IP-CIDR6": "IP-CIDR6",
    "GEOIP": "GEOIP",
}


def parse_rules_config(config_path: Path) -> list[RuleMapping]:
    """Parse the source/target mappings used to build combined rule files."""
    mappings: list[RuleMapping] = []
    current_sources: list[str] | None = None

    with config_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped == "rules:":
                continue

            if stripped == "- source:":
                if current_sources is not None:
                    raise ValueError(
                        f"Missing target for rule mapping before line {line_number}"
                    )
                current_sources = []
                continue

            if current_sources is not None and stripped.startswith("- "):
                current_sources.append(stripped[2:].strip())
                continue

            if stripped.startswith("target:"):
                if not current_sources:
                    raise ValueError(
                        f"Target without source files at line {line_number}"
                    )
                target = stripped[len("target:") :].strip()
                if not target:
                    raise ValueError(f"Empty target at line {line_number}")
                mappings.append(RuleMapping(tuple(current_sources), target))
                current_sources = None
                continue

            raise ValueError(
                f"Unsupported config.yaml content at line {line_number}: {line.rstrip()}"
            )

    if current_sources is not None:
        raise ValueError("Missing target for the last rule mapping")

    return mappings


def is_link_comment(line: str) -> bool:
    """Return whether a line is a comment containing a web link."""
    normalized_line = line.lower()
    return line.lstrip().startswith("#") and any(
        marker in normalized_line for marker in ("http://", "https://", "www.")
    )


def read_rule_sections(src_path: Path) -> tuple[list[str], list[str]]:
    """Return the source header and payload lines without the payload key."""
    with src_path.open("r", encoding="utf-8") as f:
        lines = [line.rstrip("\r\n") for line in f]

    payload_indexes: list[int] = [
        index for index, line in enumerate(lines) if line.strip() == "payload:"
    ]
    if len(payload_indexes) != 1:
        raise ValueError(f"Expected one payload field in {src_path}")

    payload_index = payload_indexes[0]
    header_lines: list[str] = [
        line for line in lines[:payload_index] if not is_link_comment(line)
    ]
    payload_lines: list[str] = lines[payload_index + 1 :]

    for line in payload_lines:
        if line.strip() and not line.startswith((" ", "\t", "#")):
            raise ValueError(
                f"Only payload content is supported after payload in {src_path}"
            )

    return header_lines, payload_lines


def format_source_path(source_path: Path) -> str:
    """Format a source path for the generated target header."""
    resolved_path = source_path.resolve()
    try:
        return resolved_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return source_path.as_posix()


def merge_rule_files(source_paths: tuple[Path, ...], target_path: Path) -> None:
    """Combine source payloads into one target while preserving source comments."""
    merged_lines: list[str] = [
        "# Generated from:",
        *[f"# - {format_source_path(source_path)}" for source_path in source_paths],
        "payload:",
    ]
    for index, source_path in enumerate(source_paths):
        header_lines, payload_lines = read_rule_sections(source_path)
        merged_lines.extend(header_lines)
        merged_lines.extend(payload_lines)
        if index < len(source_paths) - 1:
            merged_lines.append("")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(merged_lines) + "\n")


def convert_line(line: str, group_name: str) -> str | None:
    """
    Converts a single line from Clash format to QuantumultX format.
    Removes inline (end-of-line) comments for better compatibility.
    """
    stripped = line.strip()

    # Empty lines remain empty: "\n" -> ""
    if not stripped:
        return ""

    # The Clash list header is omitted: "payload:\n" -> None
    if stripped == "payload:":
        return None

    # Active rules are mapped and assigned to the current group.
    # Input: "- DOMAIN-SUFFIX,example.com # note"
    # Output: "HOST-SUFFIX,example.com,Bank"
    if stripped.startswith("- "):
        rule_part = stripped[2:].split("#", 1)[0].strip()

        sub_parts = [p.strip() for p in rule_part.split(",")]
        if len(sub_parts) >= 2:
            rule_type = sub_parts[0]
            if rule_type not in RULE_TYPE_MAPPING:
                return None
            new_type = RULE_TYPE_MAPPING[rule_type]
            return f"{new_type},{sub_parts[1]},{group_name}"
        return rule_part

    # Commented-out rules with comma-separated fields stay disabled after conversion.
    # Input: "# - DOMAIN,example.com"
    # Output: "# HOST,example.com,Bank"
    if stripped.startswith("# - ") and "," in stripped:
        rule_part = stripped[4:].split("#", 1)[0].strip()

        sub_parts = [p.strip() for p in rule_part.split(",")]
        if len(sub_parts) >= 2:
            rule_type = sub_parts[0]
            if rule_type not in RULE_TYPE_MAPPING:
                return None
            new_type = RULE_TYPE_MAPPING[rule_type]
            return f"# {new_type},{sub_parts[1]},{group_name}"
        return f"# {rule_part}"

    # Other comments are normalized to one leading "#" and kept as comments.
    # Input: "  # Bank websites" -> Output: "# Bank websites"
    if stripped.startswith("#"):
        comment_text = stripped[1:].strip()
        if comment_text:
            return f"# {comment_text}"
        return "#"

    # Unknown non-comment lines pass through unchanged.
    # Input: "GEOIP,CN" -> Output: "GEOIP,CN"
    return stripped


def process_file(src_path: Path, dst_path: Path) -> None:
    """Read a Clash YAML file and write a QuantumultX list file."""
    group_name = src_path.stem

    with src_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines: list[str] = []
    for line in lines:
        converted = convert_line(line, group_name)
        if converted is not None:
            output_lines.append(converted)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with dst_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(output_lines) + "\n")


def merge_rules_from_config(config_path: Path) -> bool:
    """Build target Clash files from the mappings in config.yaml."""
    if not config_path.exists():
        print(f"Error: Rules configuration {config_path} not found.")
        return False

    config_dir = config_path.resolve().parent
    try:
        for mapping in parse_rules_config(config_path):
            source_paths: tuple[Path, ...] = tuple(
                Path(path) if Path(path).is_absolute() else config_dir / path
                for path in mapping.sources
            )
            target_path = Path(mapping.target)
            if not target_path.is_absolute():
                target_path = config_dir / target_path
            merge_rule_files(source_paths, target_path)
            print(f"Merged: {mapping.target}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}")
        return False

    return True


def convert_clash_to_quantumultx(src_dir: Path, dst_dir: Path) -> None:
    """Convert all Clash YAML files under src_dir to QuantumultX lists."""
    if not src_dir.exists():
        print(f"Error: Source directory {src_dir} not found.")
        return

    count: int = 0
    for src_file in src_dir.rglob("*.yaml"):
        rel_path = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel_path.with_suffix(".list")

        process_file(src_file, dst_file)
        print(f"Converted: {rel_path}")
        count += 1

    print(f"\nSuccessfully converted {count} files (inline comments removed).")


def main() -> None:
    if not merge_rules_from_config(PROJECT_ROOT / "config.yaml"):
        return

    convert_clash_to_quantumultx(
        PROJECT_ROOT / "Clash/providers/rules",
        PROJECT_ROOT / "QuantumultX/rules",
    )


if __name__ == "__main__":
    main()
