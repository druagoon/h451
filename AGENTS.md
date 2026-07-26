# AGENTS.md - Project Context for h451

## Project Overview

`h451` (HTTP 451 Unavailable For Legal Reasons) is a repository for managing network proxy configuration rules and associated icon assets. It primarily supports **Clash** and **QuantumultX** proxy clients.

The project structure is organized by proxy client type and assets:

- **Clash/**: Contains YAML-based rule providers.
- **QuantumultX/**: Contains `.list` formatted rule files.
- **Assets/**: Holds icons (Source and processed 144x144 versions).

## Technologies & Standards

- **Rule Formats**: YAML (Clash), Plain-text/List (QuantumultX).
- **Automation**: GNU Make, Shell Scripting.
- **Image Processing**: `sips` (macOS native tool) used for resampling icon assets.

## Directory Structure

- `Assets/IconSet/`:
  - `Source/`: High-resolution source icons.
  - `Color/`: Processed icons resized to 144x144 (used in proxy client UIs).
- `Clash/providers/rules/x/`: Categorized rule providers for Clash (e.g., Amazon, OpenAI, Twitter).
- `QuantumultX/rules/x/`: Categorized rule lists for QuantumultX.
- `scripts/convert_rules.py`: Converts Clash rules to QuantumultX lists.
- `scripts/resample.sh`: A shell script to batch process icons from `Source/` to `Color/`.
- `GNUmakefile`: Includes common dev-tools (likely part of a larger dotfiles setup).

## Common Operations

### Icon Processing

To regenerate processed icons from source images, run:

```bash
./scripts/resample.sh
```

_Note: This script requires `sips` (standard on macOS)._

### Rule Management

Rules are added or modified manually in the respective `.yaml` or `.list` files under `Clash/` or `QuantumultX/`.

- Clash rules use the `payload` format with `DOMAIN-SUFFIX` or similar tags.
- QuantumultX rules use the `HOST-SUFFIX` format.

## Development Conventions

- **Language Policy**: Conversation is in Simplified Chinese, but all source code, comments, git commits and project artifacts must be in **English**.
- **Organization**: Rules are categorized into subdirectories (e.g., `OpenAI`, `China`, `Twitter`) for easy management.
- **Version Control**: Do not commit files in ignored paths (e.g., `Clash/providers/proxies/`).
