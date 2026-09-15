#!/usr/bin/env python3

import json
import sys
from typing import Dict, List, Any

KERNEL_VERSION = "5.10"

BUILD_CONFIGS: List[Dict[str, Any]] = [
    {
        "name": f"{KERNEL_VERSION}-KSU+SUSFS",
        "kernel_version": KERNEL_VERSION,
        "KSU": "KSU",
        "KSU_COMPAT": "false",
        "KSU_SUSFS": "true",
        "C_LTO": "false",
        "No_DS": "false"
    }
]

def generate_matrix() -> Dict[str, List[Dict[str, Any]]]:
    return {"include": BUILD_CONFIGS}

def main() -> None:
    try:
        matrix = generate_matrix()
        print(f"matrix={json.dumps(matrix)}")
        print(f"::notice::Generated {len(matrix['include'])} build configurations", file=sys.stderr)
    except Exception as e:
        print(f"::error::Failed to generate matrix: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()