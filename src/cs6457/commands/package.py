import click
import zipfile
import re
from pathlib import Path
from importlib.resources import files

# === Constants ===

README_PATTERN = re.compile(r"^[A-Za-z]+_[A-Za-z]_m\d+_readme\.txt$")
REQUIRED_DIRS = ["Build", "Assets", "ProjectSettings", "Packages"]

# === Project Validation ===

def find_valid_readme(directory: Path) -> Path | None:
    for file in directory.iterdir():
        if file.is_file() and README_PATTERN.fullmatch(file.name):
            return file
    return None

def validate_project_structure(project_path: Path):
    missing_dirs = [d for d in REQUIRED_DIRS if not (project_path / d).is_dir()]
    if missing_dirs:
        raise click.ClickException(
            f"\nMissing required directories:\n  - " + "\n  - ".join(missing_dirs)
        )

    readme = find_valid_readme(project_path)
    if not readme:
        raise click.ClickException(
            "\nMissing or incorrectly named readme file.\nExpected format: <LASTNAME>_<FIRST_INITIAL>_m<INT>_readme.txt"
        )

# === Exclude Loading ===

def load_default_excludes() -> list[str]:
    resource_file = files("cs6457.resources").joinpath("default_exclude.txt")
    return [
        line.strip()
        for line in resource_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

# === Zipping Logic ===

def package_to_zip(base_path: Path, output_zip: Path, excludes: list[str], verbose: bool = False) -> None:
    base_path = base_path.resolve()
    readme_file = find_valid_readme(base_path)

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # === Include README ===
        if readme_file:
            rel_path = readme_file.relative_to(base_path)
            if not should_exclude(rel_path, excludes):
                zipf.write(readme_file, arcname=rel_path)
                click.secho(f"[+] Added README: {rel_path}", fg="green", color=True)

        # === Include files from required directories ===
        for folder_name in REQUIRED_DIRS:
            folder_path = base_path / folder_name
            if not folder_path.exists():
                continue

            for file in folder_path.rglob("*"):
                if file.is_file():
                    rel_path = file.relative_to(base_path)
                    if should_exclude(rel_path, excludes):
                        if verbose:
                            click.secho(f"[-] Skipped (excluded): {rel_path}", fg="yellow", color=True)
                    else:
                        zipf.write(file, arcname=rel_path)
                        if verbose:
                            click.secho(f"[+] Added: {rel_path}", fg="green", color=True)

def should_exclude(path: Path, patterns: list[str]) -> bool:
    path_str = path.as_posix()
    return any(path.match(pattern) for pattern in patterns)

# === CLI ===

@click.command()
@click.option(
    "-p", "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Root directory of the Unity project (default: current directory)."
)
@click.option(
    "-e", "--exclude",
    multiple=True,
    help="Glob-style patterns to exclude (e.g., '*.meta', 'Library/**'). Can be passed multiple times."
)
@click.option(
    "-o", "--output",
    type=click.Path(writable=True, dir_okay=False, path_type=Path),
    help="Output zip file name. If not specified, one is generated from the readme name."
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output for file inclusion and exclusion."
)
def package(path: Path, exclude: list[str], output: Path, verbose: bool):
    """Package a Unity project into a zip archive, validating structure and excluding specified patterns."""
    click.secho("\n==> Validating project structure...", fg="blue", color=True)
    validate_project_structure(path)
    click.secho("✓ Project structure is valid.\n", fg="green", color=True)

    readme_file = find_valid_readme(path)
    if not readme_file:
        raise click.ClickException("Could not locate valid readme after validation step.")

    # === Derive output name from readme if not provided
    if output is None:
        stem = readme_file.stem  # e.g. "Burdell_G_m0_readme"
        if stem.endswith("_readme"):
            output = Path(f"{stem[:-7]}.zip")
        else:
            output = Path("package.zip")

    excludes = exclude or load_default_excludes()
    if not exclude:
        click.secho("Using default exclusion patterns from resources.\n", fg="yellow", color=True)

    click.secho("==> Packaging Info", fg="blue", color=True)
    click.secho(f"  Project Root   : {path}", fg="blue", color=True)
    click.secho(f"  Output Archive : {output}", fg="blue", color=True)
    click.secho(f"  Exclusions     : {', '.join(excludes)}\n", fg="yellow", color=True)

    package_to_zip(path, output, excludes, verbose=verbose)

    click.secho(f"\n✓ Created archive: {output}", fg="green", bold=True, color=True)
