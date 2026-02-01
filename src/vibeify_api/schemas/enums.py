from enum import Enum


class ProductIdentifierType(Enum):
    EAN = (
        "ean",
    )

    UPC = (
        "upc",
    )

    MPN = (
        "mpn",
    )

    MODEL = (
        "model",
    )