from fastapi import FastAPI
from pydantic import BaseModel
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    NamesExtractor,
    AddrExtractor,
    DatesExtractor,
    MoneyExtractor,
    Doc,
)

segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)
names_extractor = NamesExtractor(morph_vocab)
addr_extractor = AddrExtractor(morph_vocab)
dates_extractor = DatesExtractor(morph_vocab)
money_extractor = MoneyExtractor(morph_vocab)

app = FastAPI(title="natasha-server")


class Request(BaseModel):
    data: str
    tokens: bool = False


def fact_dict(fact):
    if fact is None:
        return None
    data = fact.as_dict if hasattr(fact, "as_dict") else fact.as_json
    return {k: v for k, v in data.items() if v is not None}


def matches(extractor, text):
    return [
        {"start": m.start, "stop": m.stop, "text": text[m.start:m.stop], "fact": fact_dict(m.fact)}
        for m in extractor(text)
    ]


def parse(text, with_tokens):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    doc.tag_ner(ner_tagger)
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
            "fact": fact_dict(span.fact),
        })

    result = {
        "spans": spans,
        "names": [s for s in spans if s["type"] == "PER"],
        "addresses": matches(addr_extractor, text),
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
