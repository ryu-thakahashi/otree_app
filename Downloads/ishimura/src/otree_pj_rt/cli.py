"""Console script for otree_pj_rt."""
import otree_pj_rt

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main():
    """Console script for otree_pj_rt."""
    console.print("Replace this message by putting your code into "
               "otree_pj_rt.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    


if __name__ == "__main__":
    app()
