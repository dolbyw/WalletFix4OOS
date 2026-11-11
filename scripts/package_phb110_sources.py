#!/usr/bin/env python3
"""Package the exact PHB110 files needed to reproduce the module ZIPs."""

import argparse
import hashlib
from pathlib import Path
import sys
from zipfile import ZipFile

from build_phb110 import COMPONENTS, EID_FILES, EID_ORIGINAL_RC, require_hash, zip_info


def source_files(rom_root: Path) -> list[Path]:
    files: set[Path] = set()
    for relative, expected in COMPONENTS.values():
        apk = rom_root / relative
        require_hash(apk, expected)
        for source in apk.parent.rglob("*"):
            if not source.is_file():
                continue
            if "oat" in source.relative_to(apk.parent).parts:
                continue
            if source.suffix in (".vdex", ".odex", ".art"):
                continue
            files.add(source)
    for relative, expected in list(EID_FILES.values()) + [EID_ORIGINAL_RC]:
        source = rom_root / relative
        require_hash(source, expected)
        files.add(source)
    return sorted(files, key=lambda path: path.relative_to(rom_root).as_posix())


def package(rom_root: Path, output: Path) -> None:
    files = source_files(rom_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with ZipFile(temporary, "w") as archive:
        checksums = []
        for source in files:
            name = source.relative_to(rom_root).as_posix()
            data = source.read_bytes()
            archive.writestr(zip_info(name), data)
            checksums.append(f"{hashlib.sha256(data).hexdigest()}  {name}\n")
        archive.writestr(zip_info("SHA256SUMS.txt"), "".join(checksums).encode())
    temporary.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        package(args.rom_root, args.output)
    except (ValueError, OSError) as error:
        print(f"Packaging failed: {error}", file=sys.stderr)
        return 1
    print(f"Packaged {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
