import os

def convert_line(line, group_name):
    """
    Converts a single line from Clash format to QuantumultX format.
    Removes inline (end-of-line) comments for better compatibility.
    """
    stripped = line.strip()

    # Maintain empty lines
    if not stripped:
        return ""

    # Skip 'payload:' header
    if stripped == 'payload:':
        return None

    # Mapping of Clash rule types to QuantumultX rule types
    type_mapping = {
        'DOMAIN': 'HOST',
        'DOMAIN-SUFFIX': 'HOST-SUFFIX',
        'DOMAIN-KEYWORD': 'HOST-KEYWORD',
        'IP-CIDR': 'IP-CIDR',
        'IP-CIDR6': 'IP-CIDR6',
        'GEOIP': 'GEOIP'
    }

    # Case 1: Active rule (starts with "- ")
    if stripped.startswith('- '):
        # Extract rule part only, discard anything after '#'
        rule_part = stripped[2:].split('#', 1)[0].strip()

        sub_parts = [p.strip() for p in rule_part.split(',')]
        if len(sub_parts) >= 2:
            rule_type = sub_parts[0]
            if rule_type not in type_mapping:
                return None
            new_type = type_mapping[rule_type]
            return f"{new_type},{sub_parts[1]},{group_name}"
        return rule_part

    # Case 2: Commented-out rule (starts with "# - ")
    if stripped.startswith('# - '):
        # Extract rule part only, discard additional inline comments
        rule_part = stripped[4:].split('#', 1)[0].strip()

        sub_parts = [p.strip() for p in rule_part.split(',')]
        if len(sub_parts) >= 2:
            rule_type = sub_parts[0]
            if rule_type not in type_mapping:
                return None
            new_type = type_mapping[rule_type]
            # Prepend "# " to keep the rule itself commented out
            return f"# {new_type},{sub_parts[1]},{group_name}"
        return f"# {rule_part}"

    # Case 3: Regular comment line (starts with "#")
    if stripped.startswith('#'):
        comment_text = stripped[1:].strip()
        if comment_text:
            return f"# {comment_text}"
        return "#"

    # Case 4: Any other line
    return stripped

def process_file(src_path, dst_path):
    """
    Reads a Clash YAML file and writes a QuantumultX .list file.
    """
    group_name = os.path.splitext(os.path.basename(src_path))[0]

    with open(src_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    for line in lines:
        converted = convert_line(line, group_name)
        if converted is not None:
            output_lines.append(converted)

    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(output_lines) + '\n')

def main():
    src_dir = 'Clash/providers/rules'
    dst_dir = 'QuantumultX/rules'

    if not os.path.exists(src_dir):
        print(f"Error: Source directory {src_dir} not found.")
        return

    count = 0
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.yaml'):
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, src_dir)
                dst_file = os.path.join(dst_dir, os.path.splitext(rel_path)[0] + '.list')

                process_file(src_file, dst_file)
                print(f"Converted: {rel_path}")
                count += 1

    print(f"\nSuccessfully converted {count} files (inline comments removed).")

if __name__ == "__main__":
    main()
