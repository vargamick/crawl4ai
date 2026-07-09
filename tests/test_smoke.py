"""Offline unit tests — no live network. Exercise the model (pydantic v2) and normalizer."""
import json
import pathlib

from agar_catalog.model import (
    AgarCatalogData, ProductSchema, MediaSchema, MediaType, MediaFormat,
    CategorySchema, ProductCategoryRelation,
)
from agar_catalog.normalizer import JSONNormalizer


def _catalog():
    p = ProductSchema(
        product_id="prod_x", product_name="Widget", product_url="https://ex.com/product/widget/",
        description="desc", category_ids=["cat_a"], sku="SKU1",
        attributes={"pH Level": ["7.0"], "Sizes": ["5L", "20L"]},
    )
    m = MediaSchema(media_id="med_1", product_id="prod_x", media_type=MediaType.IMAGE,
                    media_format=MediaFormat.PNG, media_url="https://ex.com/w.png", sequence_order=1)
    c = CategorySchema(category_id="cat_a", category_name="Cleaners")
    r = ProductCategoryRelation(product_id="prod_x", category_id="cat_a", primary=True)
    return AgarCatalogData(products=[p], media=[m], categories=[c], product_categories=[r])


def test_model_carries_new_fields():
    p = _catalog().products[0]
    assert p.sku == "SKU1"
    assert p.attributes["Sizes"] == ["5L", "20L"]


def test_normalizer_writes_the_file_set(tmp_path):
    norm = JSONNormalizer(str(tmp_path))
    saved = norm.save_normalized_files(_catalog(), filename_prefix="agar_")
    norm.save_legacy_format(_catalog(), filename_prefix="agar_")
    norm.save_summary_report(_catalog(), filename_prefix="agar_")
    names = "\n".join(pth.name for pth in pathlib.Path(tmp_path).glob("*.json"))
    for kind in ("products", "media", "categories", "product_categories",
                 "catalog_complete", "catalog_legacy", "summary"):
        assert kind in names, f"missing {kind} file"
    # sku survives the round-trip into the products file
    prod_file = next(pathlib.Path(tmp_path).glob("agar_products_*.json"))
    assert json.load(open(prod_file))[0]["sku"] == "SKU1"
