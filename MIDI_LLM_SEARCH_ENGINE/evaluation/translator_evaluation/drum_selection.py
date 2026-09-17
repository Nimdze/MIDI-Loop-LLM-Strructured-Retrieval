"""Balanced selection of one representative drum kit piece per feature type.

The taxonomy defines each drum stat once per kit-piece family (kick,
snare_clap, hats_cymbals, toms_others). For the routing evals, testing every
kit-piece variant is redundant (the example/paraphrase is identical except the
piece token, and the piece is stated). We pick ONE kit piece per drum base
stat, balanced so that (a) the kit-piece families get a uniform share and (b)
feature subcategories (spacing, dynamics, rhythmic density, grid, groove, ...)
are mixed across families rather than stacked on a single piece.
"""

DRUM_PIECES = ("kick", "snare_clap", "hats_cymbals", "toms_others")


def drum_piece(cname: str) -> tuple[str | None, str | None]:
    """Return (kit_piece_family, base_stat) for a drum concept, else (None, None).

    Whole-family prevalence aggregates (``drum_prevalence_<family>``) are grouped
    under a single stat ("prevalence") so the four families collapse to one
    representative, matching how per-piece stats are collapsed.
    """
    rest = cname[len("drum_"):]
    if rest.startswith("prevalence_"):
        fam = rest[len("prevalence_"):]
        if fam in DRUM_PIECES:
            return fam, "prevalence"
    for piece in DRUM_PIECES:
        if rest.startswith(piece + "_"):
            return piece, rest[len(piece) + 1:]
    return None, None


def select_drum_representatives(tax: dict) -> list[str]:
    """Return one representative ``drum_<piece>_<stat>`` concept per base stat.

    Non-piece drum concepts (e.g. ``drum_prevalence_*``) are each included once.
    The greedy assignment spreads base stats uniformly across the four
    kit-piece families and mixes feature subcategories across them.
    """
    by_stat: dict[str, dict[str, str]] = {}
    non_piece: list[str] = []
    for cname in tax:
        if not cname.startswith("drum_"):
            continue
        piece, stat = drum_piece(cname)
        if piece is None:
            non_piece.append(cname)
        else:
            by_stat.setdefault(stat, {})[piece] = cname

    piece_total = {p: 0 for p in DRUM_PIECES}
    subcat_count: dict[tuple[str, str], int] = {}
    selected: list[str] = []
    for stat, pieces in sorted(by_stat.items(), key=lambda kv: (len(kv[1]), kv[0])):
        sub = stat.split("_")[0]
        chosen = min(pieces, key=lambda p: (piece_total[p], subcat_count.get((sub, p), 0)))
        selected.append(pieces[chosen])
        piece_total[chosen] += 1
        subcat_count[(sub, chosen)] = subcat_count.get((sub, chosen), 0) + 1
    return sorted(selected + non_piece)
