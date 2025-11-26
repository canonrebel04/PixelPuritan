import os
import shutil
import asyncio
import aiohttp
import async_timeout
import time
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from pathlib import Path
from typing import List

# --- Configuration ---
API_URL = os.getenv("PIXELPURITAN_API_URL", "http://localhost:8000/v1/detect")
# REDUCED CONCURRENCY to prevent OOM on GTX 1060 / ViT Model
CONCURRENT_REQUESTS = int(os.getenv("PIXELPURITAN_CONCURRENCY", "4"))

app = typer.Typer(help="PixelPuritan Client", add_completion=False)
console = Console()

REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.6  # exponential backoff base

async def scan_file(session, file_path: Path, semaphore):
    async with semaphore:
        try:
            with open(file_path, 'rb') as f:
                # Proper multipart form with filename and content-type
                file_tuple = (file_path.name, f.read(), 'image/*')
                form = aiohttp.FormData()
                form.add_field('file', file_tuple[1], filename=file_tuple[0], content_type=file_tuple[2])

                # Retry with exponential backoff on transient failures
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        async with async_timeout.timeout(REQUEST_TIMEOUT_SECONDS):
                            async with session.post(API_URL, data=form) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    return {
                                        "path": file_path,
                                        "is_nsfw": result.get("is_nsfw", False),
                                        "confidence": result.get("confidence_percentage", 0),
                                        "error": None
                                    }
                                else:
                                    # 5xx considered transient; 4xx treated as permanent
                                    if 500 <= response.status < 600 and attempt < MAX_RETRIES:
                                        await asyncio.sleep(RETRY_BACKOFF_BASE ** attempt)
                                        continue
                                    return {"path": file_path, "error": f"HTTP {response.status}"}
                    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(RETRY_BACKOFF_BASE ** attempt)
                            continue
                        return {"path": file_path, "error": f"network/timeout: {e}"}
        except Exception as e:
            return {"path": file_path, "error": str(e)}

async def process_files(files: List[Path], move: bool):
    results = []
    safe_count = 0
    nsfw_count = 0
    error_count = 0
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    console.print(Panel(f"[bold blue]PixelPuritan: Scanning {len(files)} files...[/]", border_style="blue"))

    async with aiohttp.ClientSession() as session:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None, style="blue", complete_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task_id = progress.add_task("Scanning...", total=len(files))
            tasks = [scan_file(session, f, semaphore) for f in files]

            for f in asyncio.as_completed(tasks):
                res = await f
                results.append(res)
                progress.advance(task_id)

                if res.get("error"):
                    error_count += 1
                elif res["is_nsfw"]:
                    nsfw_count += 1
                else:
                    safe_count += 1

    return results, safe_count, nsfw_count, error_count

@app.command()
def scan(
    path: Path = typer.Argument(..., help="Path to file or directory", exists=True),
    move: bool = typer.Option(False, "--move", "-m", help="Automatically move files to ./nsfw and ./safe"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all files")
):
    # Gather Files
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
    files = []

    if path.is_file():
        files.append(path)
    else:
        files = [p for p in path.rglob("*") if p.suffix.lower() in extensions]

    if not files:
        console.print("[red]No image files found![/red]")
        raise typer.Exit()

    # Run Async Scan
    try:
        results, safe, nsfw, err = asyncio.run(process_files(files, move))
    except Exception as e:
        console.print(f"[bold red]CRITICAL ERROR: Connection refused or API crashed.[/]")
        console.print(f"Details: {e}")
        raise typer.Exit(code=1)

    # Move Files Logic
    if move and path.is_dir():
        nsfw_dir = path / "nsfw"
        safe_dir = path / "safe"
        nsfw_dir.mkdir(exist_ok=True)
        safe_dir.mkdir(exist_ok=True)

        for res in results:
            if res.get("error"): continue

            src = res["path"]
            if res["is_nsfw"]:
                dest = nsfw_dir / src.name
                shutil.move(str(src), str(dest))
                res["action"] = "Moved to /nsfw"
            else:
                dest = safe_dir / src.name
                shutil.move(str(src), str(dest))
                res["action"] = "Moved to /safe"

    # Display Stats
    console.print("\n")
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)

    grid.add_row(
        Panel(f"[bold white]{len(files)}[/]", title="Total", border_style="white"),
        Panel(f"[bold red]{nsfw}[/]", title="NSFW", border_style="red"),
        Panel(f"[bold green]{safe}[/]", title="Safe", border_style="green"),
        Panel(f"[bold yellow]{err}[/]", title="Errors", border_style="yellow"),
    )
    console.print(grid)

    # Write errors.csv for per-file errors without failing the whole batch
    if err > 0:
        errors_path = (path.parent if path.is_file() else path) / "errors.csv"
        try:
            with open(errors_path, 'w') as ef:
                ef.write("file,error\n")
                for r in results:
                    if r.get("error"):
                        ef.write(f"{r['path']},{r['error']}\n")
            console.print(f"[yellow]Wrote per-file errors to {errors_path}[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed writing errors.csv: {e}[/red]")
        # Do not exit nonzero for per-file errors; orchestrator should continue

if __name__ == "__main__":
    app()
