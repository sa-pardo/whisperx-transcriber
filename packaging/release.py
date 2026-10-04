"""Create a portable release without project credentials or their temp files."""
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED


def create_release(source: Path, destination: Path) -> int:
    count = 0
    with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for path in source.rglob("*"):
            if (not path.is_file() or path.is_symlink() or path.name == "settings.json"
                    or (path.name.startswith(".settings-") and path.suffix == ".tmp")):
                continue
            archive.write(path, path.relative_to(source))
            count += 1
    return count


if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:])
    count = create_release(source, destination)
    print(f"Packed {count} files -> {destination.stat().st_size // 1048576} MB")
