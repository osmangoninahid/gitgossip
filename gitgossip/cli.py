import typer
from rich.console import Console
from git import Repo, InvalidGitRepositoryError, NoSuchPathError
app = typer.Typer(help="GitGossip 🧠 – AI that spills the tea on your commits.")
console = Console()

@app.command()
def summarize(path: str = typer.Argument(".", help="Path to the local git repository")):
    """List recent commits in a repository."""
    try:
        repo = Repo(path)
        if repo.head.is_detached or not repo.head.is_valid():
            console.print("[red]No commits found in this repository yet.[/red]")
            raise typer.Exit()
    except (InvalidGitRepositoryError, NoSuchPathError):
        console.print(f"[red]❌ Not a valid Git repository: {path}[/red]")
        raise typer.Exit()

    console.print(f"[bold green]Analyzing repo:[/bold green] {path}\n")

    for commit in repo.iter_commits(max_count=10):
        console.print(f"[yellow]{commit.hexsha[:7]}[/yellow] [cyan]{commit.author.name}[/cyan] • {commit.committed_datetime:%Y-%m-%d}")
        console.print(f"    {commit.summary}\n")

if __name__ == "__main__":
    app()
