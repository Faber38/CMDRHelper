"""Offline reference catalogue for tradeable surface and asteroid commodities.

Journal symbols are case-folded, as in cargo.normalize_inventory.
Identity reference: https://github.com/EDCD/FDevIDs/blob/master/commodity.csv
German names checked against existing surface_mining_commodities and
https://github.com/EDCD/EDDI/blob/develop/DataDefinitions/Properties/Commodities.de.resx
Periclase Dunite retains its supplied English name pending a verified translation.
Prices are separate from identity and never imply a live market quote.
Origin evidence, exclusions and localization fallbacks: docs/mining-catalog-sources.md.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MiningCommodity:
    symbol: str
    average_price: int | None
    price_source: str | None
    origin: Literal["surface", "asteroid", "both"]

    @property
    def name_key(self):
        return "mining.commodity." + self.symbol


def value_class(price: int | None) -> str | None:
    if price is None:
        return None
    if price >= 100_000:
        return "high"
    if price >= 25_000:
        return "medium"
    return "low"


# Fixed galactic average selling prices (Cr/t), supplied by the project owner
# on 2026-09-12. This is the project's reference table, not fetched market data.
# The reference's original observation date is not supplied.
REFERENCE_SOURCE = "project-reference-2026-09-12"
MINING_COMMODITIES = (
    MiningCommodity("monazite", 268661, REFERENCE_SOURCE, "both"),
    MiningCommodity("alexandrite", 229207, REFERENCE_SOURCE, "both"),
    MiningCommodity("grandidierite", 213547, REFERENCE_SOURCE, "both"),
    MiningCommodity("iridium", 208463, REFERENCE_SOURCE, "surface"),
    MiningCommodity("periclasedunite", 204168, REFERENCE_SOURCE, "surface"),
    MiningCommodity("thortveitite", 203892, REFERENCE_SOURCE, "surface"),
    MiningCommodity("serendibite", 188438, REFERENCE_SOURCE, "both"),
    MiningCommodity("rhodplumsite", 187921, REFERENCE_SOURCE, "both"),
    MiningCommodity("diamond", 134784, REFERENCE_SOURCE, "surface"),
    MiningCommodity("lowtemperaturediamond", 130184, REFERENCE_SOURCE, "both"),
    MiningCommodity("sapphire", 128050, REFERENCE_SOURCE, "surface"),
    MiningCommodity("ruby", 110381, REFERENCE_SOURCE, "surface"),
    MiningCommodity("helium", 102861, REFERENCE_SOURCE, "surface"),
    MiningCommodity("helium3", 96223, REFERENCE_SOURCE, "surface"),
    MiningCommodity("bastnasite", 78583, REFERENCE_SOURCE, "surface"),
    MiningCommodity("platinum", 70998, REFERENCE_SOURCE, "both"),
    MiningCommodity("osmium", 56471, REFERENCE_SOURCE, "both"),
    MiningCommodity("tritium", 53311, REFERENCE_SOURCE, "both"),
    MiningCommodity("palladium", 52167, REFERENCE_SOURCE, "both"),
    MiningCommodity("gold", 48005, REFERENCE_SOURCE, "both"),
    MiningCommodity("quartzpyroxenite", 46469, REFERENCE_SOURCE, "surface"),
    MiningCommodity("deuterium", 40762, REFERENCE_SOURCE, "surface"),
    MiningCommodity("magnesite", 38198, REFERENCE_SOURCE, "surface"),
    MiningCommodity("silver", 37743, REFERENCE_SOURCE, "both"),
    MiningCommodity("olivine", 31417, REFERENCE_SOURCE, "surface"),
    MiningCommodity("samarium", 28362, REFERENCE_SOURCE, "both"),
    MiningCommodity("bertrandite", 18489, REFERENCE_SOURCE, "both"),
    MiningCommodity("tantalum", 14360, REFERENCE_SOURCE, "surface"),
    MiningCommodity("thorium", 12297, REFERENCE_SOURCE, "both"),
    MiningCommodity("uranium", 7599, REFERENCE_SOURCE, "surface"),
    MiningCommodity("titanium", 4800, REFERENCE_SOURCE, "surface"),
    MiningCommodity("uraninite", 3006, REFERENCE_SOURCE, "both"),
    MiningCommodity("haematite", 2800, REFERENCE_SOURCE, "surface"),
    MiningCommodity("methanolmonohydratecrystals", 2525, REFERENCE_SOURCE, "both"),
    MiningCommodity("lithium", 2099, REFERENCE_SOURCE, "surface"),
    MiningCommodity("copper", 774, REFERENCE_SOURCE, "surface"),
    MiningCommodity("water", 496, REFERENCE_SOURCE, "both"),
    # New observations: only Jadeite has an owner-verified average price.
    MiningCommodity("jadeite", 41895, "owner-elite-screenshot-2026-09-12", "surface"),
    MiningCommodity("taaffeite", None, None, "surface"),
    MiningCommodity("moissanite", None, None, "surface"),
    MiningCommodity("bauxite", None, None, "asteroid"),
    MiningCommodity("benitoite", None, None, "asteroid"),
    MiningCommodity("bromellite", None, None, "asteroid"),
    MiningCommodity("cobalt", None, None, "asteroid"),
    MiningCommodity("coltan", None, None, "asteroid"),
    MiningCommodity("gallite", None, None, "asteroid"),
    MiningCommodity("hydrogenperoxide", None, None, "asteroid"),
    MiningCommodity("indite", None, None, "asteroid"),
    MiningCommodity("lepidolite", None, None, "asteroid"),
    MiningCommodity("liquidoxygen", None, None, "asteroid"),
    MiningCommodity("lithiumhydroxide", None, None, "asteroid"),
    MiningCommodity("methaneclathrate", None, None, "asteroid"),
    MiningCommodity("musgravite", None, None, "asteroid"),
    MiningCommodity("opal", None, None, "asteroid"),
    MiningCommodity("painite", None, None, "asteroid"),
    MiningCommodity("praseodymium", None, None, "asteroid"),
    MiningCommodity("rutile", None, None, "asteroid"),
)
