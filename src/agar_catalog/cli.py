"""`harvest` CLI — API-first product-catalogue harvester."""
from __future__ import annotations
import pathlib
from typing import Optional

import typer

from .config import ClientConfig
from .pipeline import harvest as run_harvest
from . import compare as _compare

app = typer.Typer(add_completion=False, help="API-first Agar catalogue harvester.")


def _config(client: str) -> ClientConfig:
    path = pathlib.Path("clients") / f"{client}.yaml"
    if not path.exists():
        raise typer.BadParameter(f"no client config at {path}")
    return ClientConfig.load(path)


@app.command()
def run(
    client: str = typer.Option("agar", help="Client config name (clients/<name>.yaml)."),
    source: Optional[str] = typer.Option(None, help="Override source (store_api)."),
    limit: Optional[int] = typer.Option(None, help="Cap number of products."),
    out: Optional[str] = typer.Option(None, help="Output directory."),
    documents: bool = typer.Option(True, help="Fetch SDS/PDS document links per product."),
):
    """Harvest the catalogue and write the 8-file 3DN output set + markdown."""
    cfg = _config(client)
    catalog, saved = run_harvest(cfg, source=source, limit=limit,
                                 include_documents=documents, output_dir=out)
    typer.echo(f"products={len(catalog.products)} media={len(catalog.media)} "
               f"documents={len(catalog.documents)} categories={len(catalog.categories)} "
               f"relationships={len(catalog.product_categories)}")
    for k, v in saved.items():
        typer.echo(f"  {k}: {v}")


@app.command()
def compare(
    client: str = typer.Option("agar", help="Client config name."),
    knowledge_store: str = typer.Option("tests/fixtures/baseline_0.7.4",
                                        help="Dir or JSON of the current knowledge store."),
    limit: Optional[int] = typer.Option(None),
):
    """Reconcile a fresh harvest against the knowledge store; highlight conflicting values."""
    cfg = _config(client)
    catalog, _ = run_harvest(cfg, limit=limit, include_documents=False, write=False)
    rep = _compare.reconcile(_compare.catalog_records(catalog),
                             _compare.knowledge_records(knowledge_store))
    _compare.print_report(rep)


if __name__ == "__main__":
    app()
