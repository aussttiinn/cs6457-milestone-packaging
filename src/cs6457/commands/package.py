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
            f"Missing required directories: {', '.join(missing_dirs)}"
        )

    readme = find_valid_readme(project_path)
    if not readme:
        raise click.ClickException(
            "Missing or incorrectly named readme file.\nExpected pattern: <LASTNAME>_<FIRST_INITIAL>_m<INT>_readme.txt"
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
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in base_path.rglob("*"):
            if file.is_file():
                rel_path = file.relative_to(base_path)
                if should_exclude(rel_path, excludes):
                    if verbose:
                        click.secho(f"  [excluded] {rel_path}", fg="yellow", color=True)
                else:
                    zipf.write(file, arcname=rel_path)
                    if verbose:
                        click.secho(f"  [included] {rel_path}", fg="green", color=True)

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
    default="package.zip",
    type=click.Path(writable=True, dir_okay=False, path_type=Path),
    help="Output zip file name (default: package.zip)."
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output for file inclusion and exclusion."
)
def package(path: Path, exclude: list[str], output: Path, verbose: bool):
    """Package a Unity project into a zip archive, validating structure and excluding specified patterns."""
    click.secho("Validating project structure...", fg="blue", color=True)
    validate_project_structure(path)
    click.secho("Structure validated.\n", fg="green", color=True)

    excludes = exclude or load_default_excludes()
    if not exclude:
        click.secho("Using default exclusion patterns from resources.\n", fg="yellow", color=True)

    click.secho(f"Project root        : {path}", fg="blue", color=True)
    click.secho(f"Output zip          : {output}", fg="blue", color=True)
    click.secho(f"Exclusion patterns  : {excludes}\n", fg="yellow", color=True)

    package_to_zip(path, output, excludes, verbose=verbose)

    click.secho("Packaging complete.", fg="green", bold=True, color=True)
