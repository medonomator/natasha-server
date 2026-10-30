import os

from fastapi import FastAPI
from pydantic import BaseModel, Field
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    NamesExtractor,
    DatesExtractor,
    MoneyExtractor,
    Doc,
)

from addresses import extract_addresses

segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)
names_extractor = NamesExtractor(morph_vocab)
dates_extractor = DatesExtractor(morph_vocab)
money_extractor = MoneyExtractor(morph_vocab)

MAX_TEXT_LENGTH = int(os.environ.get("MAX_TEXT_LENGTH", "20000"))

app = FastAPI(title="natasha-server")


class Request(BaseModel):
    data: str = Field(max_length=MAX_TEXT_LENGTH)
    tokens: bool = False


def drop_none(data):
    return {k: v for k, v in data.items() if v is not None}


def matches(extractor, text):
    return [
        {"start": m.start, "stop": m.stop, "text": text[m.start:m.stop], "fact": drop_none(m.fact.as_json)}
        for m in extractor(text)
    ]


def parse(text, with_tokens):
    doc = Doc(text)
    doc.segment(segmenter)
    if not doc.tokens:
        result = {"spans": [], "names": [], "addresses": [], "dates": [], "money": []}
        if with_tokens:
            result["tokens"] = []
        return result

    doc.tag_morph(morph_tagger)
    doc.tag_ner(ner_tagger)
    if with_tokens:
        doc.parse_syntax(syntax_parser)
        for token in doc.tokens:
            token.lemmatize(morph_vocab)

    spans = []
    for span in doc.spans:
        span.normalize(morph_vocab)
        if span.type == "PER":
            span.extract_fact(names_extractor)
        spans.append({
            "type": span.type,
            "start": span.start,
            "stop": span.stop,
            "text": span.text,
            "normal": span.normal,
            "fact": drop_none(span.fact.as_dict) if span.fact else None,
        })

    result = {
        "spans": spans,
        "names": [
            {
                "first": s["fact"].get("first"),
                "last": s["fact"].get("last"),
                "middle": s["fact"].get("middle"),
            }
            for s in spans
            if s["type"] == "PER" and s["fact"]
        ],
        "addresses": extract_addresses(text),
        "dates": matches(dates_extractor, text),
        "money": matches(money_extractor, text),
    }
    if with_tokens:
        result["tokens"] = [
            {
                "text": t.text,
                "start": t.start,
                "stop": t.stop,
                "lemma": t.lemma,
                "pos": t.pos,
                "feats": t.feats,
                "head_id": t.head_id,
                "rel": t.rel,
            }
            for t in doc.tokens
        ]
    return result


@app.post("/natasha")
def natasha(req: Request):
    return {"original_data": req.model_dump(), **parse(req.data, req.tokens)}


@app.get("/health")
def health():
    return {"status": "ok"}
