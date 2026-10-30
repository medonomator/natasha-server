import re

from pullenti.morph.MorphLang import MorphLang
from pullenti.ner.ProcessorService import ProcessorService
from pullenti.ner.SourceOfAnalysis import SourceOfAnalysis
from pullenti.ner.core.MiscHelper import MiscHelper
from pullenti.ner.geo.GeoAnalyzer import GeoAnalyzer
from pullenti.ner.address.AddressAnalyzer import AddressAnalyzer
from pullenti.ner.address.AddressReferent import AddressReferent
from pullenti.ner.address.StreetReferent import StreetReferent

ProcessorService.initialize(MorphLang.RU)
GeoAnalyzer.initialize()
AddressAnalyzer.initialize()

ANALYZERS = ",".join([GeoAnalyzer.ANALYZER_NAME, AddressAnalyzer.ANALYZER_NAME])

NON_BMP = re.compile("[\U00010000-\U0010FFFF]")

FIELDS = {
    "zip": AddressReferent.ATTR_ZIP,
    "house": AddressReferent.ATTR_HOUSE,
    "corpus": AddressReferent.ATTR_CORPUS,
    "building": AddressReferent.ATTR_BUILDING,
    "flat": AddressReferent.ATTR_FLAT,
    "office": AddressReferent.ATTR_OFFICE,
    "plot": AddressReferent.ATTR_PLOT,
    "block": AddressReferent.ATTR_BLOCK,
    "box": AddressReferent.ATTR_BOX,
    "porch": AddressReferent.ATTR_PORCH,
    "floor": AddressReferent.ATTR_FLOOR,
    "kilometer": AddressReferent.ATTR_KILOMETER,
}


def geo_chain(geo):
    chain = []
    while geo is not None:
        chain.append({"type": geo.typs[0] if geo.typs else None, "name": geo.to_string(True)})
        geo = geo.higher
    return list(reversed(chain))


def address_geo(address):
    geo = address.get_slot_value(AddressReferent.ATTR_GEO)
    if geo is not None:
        return geo
    for street in address.streets:
        if street.city is not None:
            return street.city
    return None


def street_name(street):
    parts = [street.number, street.sec_number]
    name = street.get_string_value(StreetReferent.ATTR_NAME)
    if name is not None:
        parts.append(MiscHelper.convert_first_char_upper_and_other_lower(name))
    return " ".join(p for p in parts if p) or None


def to_dict(address, text, occurrence):
    result = {
        "start": occurrence.begin_char,
        "stop": occurrence.end_char + 1,
        "text": text[occurrence.begin_char:occurrence.end_char + 1],
        "normal": address.to_string(False),
        "geo": geo_chain(address_geo(address)),
        "streets": [
            {"type": s.typs[0] if s.typs else None, "name": street_name(s)}
            for s in address.streets
        ],
    }
    for key, attr in FIELDS.items():
        value = address.get_string_value(attr)
        if value is not None:
            result[key] = value
    return result


def extract_addresses(text):
    processor = ProcessorService.create_specific_processor(ANALYZERS)
    result = processor.process(SourceOfAnalysis(NON_BMP.sub("�", text)))
    addresses = [
        to_dict(entity, text, occurrence)
        for entity in result.entities
        if isinstance(entity, AddressReferent)
        for occurrence in entity.occurrence
    ]
    return sorted(addresses, key=lambda a: a["start"])
