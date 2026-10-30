from pullenti.morph.MorphLang import MorphLang
from pullenti.ner.ProcessorService import ProcessorService
from pullenti.ner.SourceOfAnalysis import SourceOfAnalysis
from pullenti.ner.geo.GeoAnalyzer import GeoAnalyzer
from pullenti.ner.address.AddressAnalyzer import AddressAnalyzer
from pullenti.ner.address.AddressReferent import AddressReferent

ProcessorService.initialize(MorphLang.RU)
GeoAnalyzer.initialize()
AddressAnalyzer.initialize()

ANALYZERS = ",".join([GeoAnalyzer.ANALYZER_NAME, AddressAnalyzer.ANALYZER_NAME])

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
    if geo is None:
        for street in address.streets:
            geo = street.get_slot_value("GEO")
            if geo is not None:
                break
    return geo


def to_dict(address, text):
    occurrence = address.occurrence[0]
    result = {
        "start": occurrence.begin_char,
        "stop": occurrence.end_char + 1,
        "text": text[occurrence.begin_char:occurrence.end_char + 1],
        "normal": address.to_string(False),
        "geo": geo_chain(address_geo(address)),
        "streets": [
            {"type": s.typs[0] if s.typs else None, "name": s.names[0].title() if s.names else None}
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
    result = processor.process(SourceOfAnalysis(text))
    return [to_dict(e, text) for e in result.entities if isinstance(e, AddressReferent)]
