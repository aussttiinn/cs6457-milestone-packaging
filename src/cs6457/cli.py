import click
from cs6457.commands import package

@click.group()
def main():
    """CLI for packaging milestones for CS6457 unity projects."""
    pass

main.add_command(package.package)