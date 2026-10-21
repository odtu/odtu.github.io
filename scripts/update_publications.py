#!/usr/bin/env python3
"""Fetch PowerLab publications from OpenAlex and write _data/publications.yml.

Runs monthly from .github/workflows/update-publications.yml, or by hand:
    pip install pyyaml
    python scripts/update_publications.py

Settings (who to include, exclusions) live in scripts/publications_config.yml.
Papers OpenAlex misses can be added by hand to _data/publications_manual.yml.
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "scripts" / "publications_config.yml"
OUT = ROOT / "_data" / "publications.yml"
META = ROOT / "_data" / "publications_meta.yml"
MANUAL = ROOT / "_data" / "publications_manual.yml"
API = "https://api.openalex.org"

KEEP_TYPES = {"article", "book-chapter", "book", "review", "letter"}
CONF_WORDS = re.compile(
    r"conference|symposium|congress|workshop|proceedings|convention|"
    r"powertech|\becce\b|\biecon\b|\bapec\b|\bicem\b|\biemdc\b|\bpemd\b|\bpedg\b",
    re.I,
)


def load_yaml(path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return default if data is None else data


def api_get(path, params, cfg):
    params = dict(params)
    if cfg.get("mailto"):
        params["mailto"] = cfg["mailto"]
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    url = f"{API}{path}?{urllib.parse.urlencode(params, safe=':|,*')}"
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "powerlab-website"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            body = e.read()[:300].decode("utf-8", "replace")
            print(f"HTTP {e.code} from {path}: {body}", flush=True)
            if attempt == 4:
                raise RuntimeError(f"OpenAlex HTTP {e.code} on {path}: {body}")
        except urllib.error.URLError:
            if attempt == 4:
                raise
        time.sleep(2 ** attempt)


def resolve_author_ids(pi, cfg):
    ids = [i.rsplit("/", 1)[-1] for i in pi.get("openalex_ids") or []]
    orcid = (pi.get("orcid") or "").strip()
    if orcid:
        orcid = orcid.rsplit("/", 1)[-1]
        author = api_get(f"/authors/orcid:{orcid}", {}, cfg)
        if author:
            ids.append(author["id"].rsplit("/", 1)[-1])
        else:
            print(f"WARNING: no OpenAlex author for ORCID {orcid} ({pi['name']})")
    return sorted(set(ids))


def fetch_works(author_ids, cfg):
    works, cursor = [], "*"
    filt = f"author.id:{'|'.join(author_ids)},is_paratext:false"
    if cfg.get("min_year"):
        filt += f",from_publication_date:{cfg['min_year']}-01-01"
    while cursor:
        page = api_get("/works", {"filter": filt, "per-page": 200, "cursor": cursor}, cfg)
        works.extend(page["results"])
        cursor = page["meta"].get("next_cursor")
        if not page["results"]:
            break
    return works


def short_name(name):
    """'Mehmet Can Kulan' -> 'M. C. Kulan'."""
    name = re.sub(r"\s+", " ", name or "").strip()
    parts = name.split(" ")
    if len(parts) < 2:
        return name
    initials = []
    for p in parts[:-1]:
        sub = [s for s in p.split("-") if s]
        initials.append("-".join(s[0].upper() + "." for s in sub))
    return " ".join(initials + [parts[-1]])


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", "", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", clean(t).lower())


def classify(work, source):
    wtype = work.get("type")
    if wtype in ("book-chapter", "book"):
        return "book"
    stype = (source or {}).get("type") or ""
    name = (source or {}).get("display_name") or ""
    if stype == "conference" or CONF_WORDS.search(name):
        return "conference"
    if stype == "journal":
        return "journal"
    return "other"


def pick_source(work):
    locs = [work.get("primary_location")] + (work.get("locations") or [])
    for loc in locs:
        src = (loc or {}).get("source")
        if src and src.get("type") != "repository":
            return loc, src
    loc = work.get("primary_location") or {}
    return loc, loc.get("source")


def convert(work, pis_by_author, cfg):
    if work.get("is_retracted") or work.get("type") not in KEEP_TYPES:
        return None
    year = work.get("publication_year")
    inst = cfg.get("institution", "")

    # Count the paper only if a PI wrote it while at METU.
    pis = []
    for a in work.get("authorships") or []:
        aid = ((a.get("author") or {}).get("id") or "").rsplit("/", 1)[-1]
        pi = pis_by_author.get(aid)
        if not pi:
            continue
        insts = [i.get("id", "").rsplit("/", 1)[-1] for i in a.get("institutions") or []]
        lineage = [l.rsplit("/", 1)[-1] for i in a.get("institutions") or [] for l in i.get("lineage") or []]
        at_inst = inst in insts or inst in lineage
        no_info = not insts
        if at_inst or (no_info and year and year >= int(pi.get("since") or 0)):
            if pi["name"] not in pis:
                pis.append(pi["name"])
    if not pis:
        return None

    loc, source = pick_source(work)
    kind = classify(work, source)
    if kind == "other" and not cfg.get("include_other", False):
        return None

    names, last_pi = [], 0
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        aid = (author.get("id") or "").rsplit("/", 1)[-1]
        n = html.escape(short_name(author.get("display_name") or a.get("raw_author_name") or ""))
        if aid in pis_by_author:
            n, last_pi = f"<b>{n}</b>", len(names) + 1
        names.append(n)
    max_authors = int(cfg.get("max_authors", 10))
    if len(names) > max_authors:
        cut = max(max_authors - 2, last_pi)  # never cut a PI off the list
        if cut < len(names):
            names = names[:cut] + ["et al."]

    doi = (work.get("doi") or "").replace("https://doi.org/", "") or None
    oa = work.get("best_oa_location") or {}
    pdf = oa.get("pdf_url") or (work.get("open_access") or {}).get("oa_url")
    url = f"https://doi.org/{doi}" if doi else (loc or {}).get("landing_page_url") or work.get("id")
    if pdf and doi and doi.lower() in pdf.lower():
        pdf = None  # the DOI link already leads to the free version

    return {
        "title": clean(work.get("display_name") or work.get("title")),
        "authors": ", ".join(names),
        "venue": clean((source or {}).get("display_name")) or None,
        "kind": kind,
        "year": year,
        "date": work.get("publication_date"),
        "doi": doi,
        "url": url,
        "pdf": pdf,
        "cites": work.get("cited_by_count") or 0,
        "pis": pis,
        "openalex": work.get("id", "").rsplit("/", 1)[-1] or None,
    }


def excluded(pub, cfg):
    doi = (pub.get("doi") or "").lower()
    if doi and doi in {d.lower() for d in cfg.get("exclude_dois") or []}:
        return True
    title = (pub.get("title") or "").lower()
    return any(t.lower() in title for t in cfg.get("exclude_titles") or [])


def dedupe(pubs):
    rank = {"journal": 0, "conference": 1, "book": 2, "other": 3}
    best = {}
    for p in pubs:
        key = (p.get("doi") or "").lower() or norm_title(p["title"])
        tkey = norm_title(p["title"])
        for k in {key, tkey}:
            if k in best:
                old = best[k]
                score_new = (p.get("doi") is None, rank[p["kind"]], -p["cites"])
                score_old = (old.get("doi") is None, rank[old["kind"]], -old["cites"])
                if score_new < score_old:
                    p["cites"] = max(p["cites"], old["cites"])
                    best[k] = p
                else:
                    old["cites"] = max(p["cites"], old["cites"])
                break
        else:
            best[tkey] = p
    seen, out = set(), []
    for p in best.values():
        if id(p) not in seen:
            seen.add(id(p))
            out.append(p)
    return out


def main():
    cfg = load_yaml(CONFIG, {})
    pis_by_author = {}
    for pi in cfg.get("pis") or []:
        ids = resolve_author_ids(pi, cfg)
        if not ids:
            print(f"WARNING: {pi['name']} has no ORCID/OpenAlex id yet - skipped")
        for aid in ids:
            pis_by_author[aid] = pi
    if not pis_by_author:
        sys.exit("No PI could be resolved; nothing written.")

    works = fetch_works(sorted(pis_by_author), cfg)
    print(f"OpenAlex returned {len(works)} works")
    pubs = [p for w in works if (p := convert(w, pis_by_author, cfg)) and not excluded(p, cfg)]

    manual = load_yaml(MANUAL, []) or []
    for m in manual:
        m.setdefault("cites", 0)
        m.setdefault("kind", "journal")
        m.setdefault("pis", [])
        m["manual"] = True
    pubs = dedupe(manual + pubs)
    pubs.sort(key=lambda p: (p.get("date") or f"{p.get('year', 0)}-00-00", p["title"]), reverse=True)

    old = load_yaml(OUT, [])
    if old and len(pubs) < 0.7 * len(old):
        sys.exit(f"Only {len(pubs)} papers vs {len(old)} before - looks like an API problem; nothing written.")
    if pubs == old:
        print("No changes.")
        return

    header = (
        "# AUTO-GENERATED by scripts/update_publications.py from OpenAlex - do not edit by hand.\n"
        "# To add a missing paper use _data/publications_manual.yml;\n"
        "# to hide one, add its DOI to exclude_dois in scripts/publications_config.yml.\n"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(pubs, f, allow_unicode=True, sort_keys=False, width=1000)
    counts = {k: sum(p["kind"] == k for p in pubs) for k in ("journal", "conference", "book", "other")}
    with open(META, "w", encoding="utf-8") as f:
        yaml.safe_dump({"updated": datetime.date.today().isoformat(), "total": len(pubs), **counts},
                       f, sort_keys=False)
    print(f"Wrote {len(pubs)} publications: {counts}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"::error::{e.code}")
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = f"{type(e).__name__}: {e}".replace("\n", " ")[:500]
        print(f"::error::{msg}")
        sys.exit(1)
