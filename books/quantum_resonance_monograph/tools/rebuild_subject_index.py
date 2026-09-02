#!/usr/bin/env python3
"""Rebuild curated subject-index anchors on substantive chapter pages.

The glossary is an alphabetical reading aid, not the subject index.  This
script removes direct index locators from the glossary and inserts generated,
clearly delimited locator blocks at the beginning of relevant sections and
subsections.  Terms are curated below; section titles are never turned into
index keys automatically.

The operation is idempotent.  Re-running the script first removes only blocks
which it generated previously.  Hand-written ``\\index`` and ``\\term``
commands elsewhere are preserved.
"""

from __future__ import annotations

import re
from pathlib import Path


BEGIN = "% BEGIN CURATED SUBJECT INDEX"
END = "% END CURATED SUBJECT INDEX"

# A regular expression is matched against one semantic section block.  The
# second field is the stable makeindex key.  Patterns deliberately favor
# precision over recall; a term absent here should be added by editorial
# judgment rather than inferred from a heading string.
TERMS: tuple[tuple[str, str], ...] = (
    (r"adjoint|self-adjoint", "operator!adjoint and self-adjoint"),
    (r"self-adjoint extension|deficiency", "self-adjoint extension"),
    (r"unbounded operator|operator domain|domain is part", "unbounded operator"),
    (r"closed operator|closable", "operator!closed"),
    (r"Banach", "Banach space"),
    (r"Hilbert space", "Hilbert space"),
    (r"locally convex|seminorm|test space", "locally convex space"),
    (r"topolog(?:y|ical)|convergence means", "topology"),
    (r"measure space|measurable|almost everywhere", "measure theory"),
    (r"spectral theorem|projection-valued", "spectral theorem"),
    (r"spectral measure", "spectral measure"),
    (r"continuous spectrum", "spectrum!continuous"),
    (r"essential spectrum", "spectrum!essential"),
    (r"point spectrum|eigenvalue", "spectrum!point"),
    (r"resolvent", "resolvent"),
    (r"resolvent set", "resolvent set"),
    (r"Riesz projection", "Riesz projection"),
    (r"pseudospect", "pseudospectrum"),
    (r"direct integral", "direct integral"),
    (r"fiber Hilbert|multiplicity fiber|energy fiber", "direct integral!fiber"),
    (r"decomposable", "decomposable operator"),
    (r"commutant", "commutant"),
    (r"von\\~Neumann|\\vN", "von Neumann algebra@\\vN\\ algebra"),
    (r"central decomposition|center of", "central decomposition"),
    (r"factor representation|factor decomposition", "factor"),
    (r"superselection", "superselection sector"),
    (r"GNS|Gelfand--Naimark", "GNS construction"),
    (r"state on (?:an|a) algebra|positive linear functional", "state!operator algebra"),
    (r"compact operator|compactness", "compact operator"),
    (r"Hilbert--Schmidt", "Hilbert--Schmidt operator"),
    (r"trace class|trace-class", "trace-class operator"),
    (r"Fredholm", "Fredholm theory"),
    (r"Birman--Schwinger", "Birman--Schwinger operator"),
    (r"regularized determinant|Fredholm determinant", "Fredholm determinant"),
    (r"Sturm--Liouville", "Sturm--Liouville theory"),
    (r"limit point|limit circle", "Sturm--Liouville theory!limit-point/limit-circle"),
    (r"Weyl--Titchmarsh", "Weyl--Titchmarsh function"),
    (r"Jost", "Jost function"),
    (r"Wronskian", "Wronskian"),
    (r"wave packet", "wave packet"),
    (r"wave operator|M\\o ller", "wave operator"),
    (r"asymptotic completeness", "asymptotic completeness"),
    (r"Lippmann--Schwinger", "Lippmann--Schwinger equation"),
    (r"Born approximation|Born amplitude", "Born approximation"),
    (r"optical theorem", "optical theorem"),
    (r"cross section", "cross section"),
    (r"partial wave", "partial-wave expansion"),
    (r"phase shift", "phase shift"),
    (r"time delay", "Wigner time delay"),
    (r"threshold law|threshold behavior|threshold data", "threshold law"),
    (r"S matrix|scattering matrix|\\Scattering", "scattering matrix"),
    (r"on-shell", "scattering!on-shell"),
    (r"channel multiplicity|multichannel", "scattering!multichannel"),
    (r"connection coefficient|connection matrix|\\Cincoming", "connection coefficient"),
    (r"incoming|outgoing", "boundary condition!incoming and outgoing"),
    (r"Riemann (?:sheet|surface)|physical sheet|second sheet", "Riemann sheet"),
    (r"branch cut", "branch cut"),
    (r"pole residue|residue", "resonance!residue"),
    (r"Gamow|Siegert", "Gamow--Siegert state"),
    (r"antiresonance", "antiresonance"),
    (r"Breit--Wigner", "Breit--Wigner approximation"),
    (r"Fano", "Fano profile"),
    (r"nonexponential|non-exponential", "decay!nonexponential"),
    (r"Coulomb", "scattering!Coulomb"),
    (r"Coulomb plane wave", "Coulomb plane wave"),
    (r"Dollard", "Dollard comparison dynamics"),
    (r"three-body Coulomb|three charged", "scattering!three-body Coulomb"),
    (r"infrared|soft photon", "infrared problem"),
    (r"dressing|dressed state", "dressing state"),
    (r"Fock space", "Fock space!infrared limitation"),
    (r"Gauss law", "Gauss law"),
    (r"BRST", "BRST cohomology"),
    (r"Gribov", "Gribov problem"),
    (r"observable algebra", "observable algebra"),
    (r"AQFT|algebraic quantum field", "algebraic quantum field theory"),
    (r"tensor-product|tensor product", "tensor product!gauge constraint"),
    (r"Borel transform", "Borel transform"),
    (r"Borel sum|Borel resumm", "Borel summation"),
    (r"lateral sum|lateral resumm", "lateral Borel sum"),
    (r"Borel plane|Borel singular", "Borel plane"),
    (r"Stokes curve|Stokes line", "Stokes curve"),
    (r"Stokes matrix", "Stokes matrix"),
    (r"Stokes automorphism", "Stokes automorphism"),
    (r"turning point", "turning point"),
    (r"Riccati", "Riccati equation"),
    (r"formal WKB|exact WKB", "exact WKB"),
    (r"Voros symbol|Voros period", "Voros symbol"),
    (r"quantization condition", "exact quantization condition"),
    (r"monodromy", "monodromy"),
    (r"Langer", "Langer correction"),
    (r"Frobenius", "Frobenius solution"),
    (r"radial equation|radial Schr", "radial equation"),
    (r"Rosen--Morse", "Rosen--Morse potential"),
    (r"complex scaling", "complex scaling"),
    (r"analytic dilation", "analytic dilation"),
    (r"Aguilar--Balslev--Combes|ABC theorem", "Aguilar--Balslev--Combes theorem"),
    (r"exterior complex scaling", "complex scaling!exterior"),
    (r"smooth complex scaling", "complex scaling!smooth"),
    (r"complex absorbing", "complex absorbing potential"),
    (r"biorthogon", "biorthogonality"),
    (r"complex symmetric|complex-symmetric", "complex-symmetric operator"),
    (r"Zel['’]dovich", "Zel'dovich regularization"),
    (r"Gaussian regularization", "Gaussian regularization"),
    (r"Berggren", "Berggren completeness relation"),
    (r"rigged Hilbert|Gelfand triple", "rigged Hilbert space"),
    (r"Hardy class", "Hardy class"),
    (r"continuum level density", "continuum level density"),
    (r"spectral shift", "spectral shift function"),
    (r"pseudostate", "pseudostate"),
    (r"stabilization", "stabilization method"),
    (r"Feshbach", "Feshbach projection"),
    (r"effective Hamiltonian", "effective Hamiltonian"),
    (r"self-energy", "self-energy"),
    (r"optical potential", "optical potential"),
    (r"R-matrix", "R-matrix@$R$-matrix"),
    (r"Jacobi", "Jacobi coordinate"),
    (r"antisymmetr", "antisymmetrization"),
    (r"coupled channel", "coupled-channel equation"),
    (r"distorted wave", "distorted-wave approximation"),
    (r"Faddeev", "Faddeev equation"),
    (r"eikonal", "eikonal approximation"),
    (r"adiabatic", "adiabatic approximation"),
    (r"CDCC|continuum-discretized", "CDCC"),
    (r"bin discret", "CDCC!bin discretization"),
    (r"Gaussian expansion", "Gaussian expansion method"),
    (r"four-body CDCC|three-cluster", "CDCC!four-body"),
    (r"folding", "folding interaction"),
    (r"transition density", "transition density"),
    (r"breakup", "nuclear breakup"),
    (r"lithium|\\^\{?\d+\}?Li", "lithium nuclei"),
    (r"beryllium|\\^\{?\d+\}?Be", "beryllium nuclei"),
    (r"helium|\\^6He", "helium-6@${}^6$He"),
    (r"exceptional point|\bEP\b", "exceptional point"),
    (r"Jordan chain|Jordan block", "Jordan chain"),
    (r"defective|defectiveness", "exceptional point!defectiveness"),
    (r"self-orthogon", "self-orthogonality"),
    (r"Berry connection|geometric phase", "geometric phase"),
    (r"holonomy", "holonomy"),
    (r"Chern", "Chern number"),
    (r"momentum bin", "momentum-bin regularization"),
    (r"renormalization group|running coupling|regulator independence", "renormalization group"),
    (r"quasinormal|\bQNM", "quasinormal mode"),
    (r"Regge--Wheeler", "Regge--Wheeler equation"),
    (r"Zerilli", "Zerilli equation"),
    (r"tortoise", "tortoise coordinate"),
    (r"horizon", "horizon boundary condition"),
    (r"Schwarzschild", "Schwarzschild black hole"),
    (r"Reissner--Nordstr", "Reissner--Nordstr\\\"om black hole"),
    (r"de Sitter", "de Sitter spacetime"),
    (r"Kerr", "Kerr black hole"),
    (r"superradi", "superradiance"),
    (r"Teukolsky", "Teukolsky equation"),
    (r"late-time tail|late time tail", "late-time tail"),
    (r"excitation factor", "quasinormal mode!excitation factor"),
    (r"continuum response|response function", "continuum response"),
    (r"optimized perturbation", "optimized perturbation theory"),
    (r"variational perturbation", "variational perturbation theory"),
    (r"minimal sensitivity|\bPMS\b", "principle of minimal sensitivity"),
    (r"order-dependent mapping|\bODM\b", "order-dependent mapping"),
    (r"Pad\\'e", "Pad\\'e approximant"),
    (r"instanton", "instanton"),
    (r"large order|large-order", "large-order behavior"),
    (r"transseries|trans-series", "transseries"),
)

HEADING = re.compile(r"(?m)^\\(?:chapter|section|subsection|subsubsection)\*?\{")
GENERATED = re.compile(
    rf"(?ms)^\s*{re.escape(BEGIN)}\n.*?^\s*{re.escape(END)}\n?"
)
DIRECT_INDEX = re.compile(r"\s*\\index\{[^{}]*\}")


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    for position in range(opening, len(text)):
        if text[position] == "{" and (position == 0 or text[position - 1] != "\\"):
            depth += 1
        elif text[position] == "}" and (position == 0 or text[position - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return position
    raise ValueError(f"unbalanced heading at byte {opening}")


def insertion_point(text: str, heading_end: int, block_end: int) -> int:
    """Insert after a nearby label so hyperlinks and locators share a page."""
    tail = text[heading_end:block_end]
    label = re.match(r"(?s)(\s*\\label\{[^{}]+\})", tail)
    return heading_end + (label.end() if label else 0)


def rebuild_file(path: Path) -> int:
    original = path.read_text(encoding="utf-8")
    text = GENERATED.sub("", original)
    headings = list(HEADING.finditer(text))
    additions: list[tuple[int, str]] = []
    total = 0
    for number, heading in enumerate(headings):
        opening = text.find("{", heading.start())
        close = matching_brace(text, opening)
        heading_end = close + 1
        block_end = headings[number + 1].start() if number + 1 < len(headings) else len(text)
        block = text[heading.start():block_end]
        keys = [key for pattern, key in TERMS if re.search(pattern, block, re.I)]
        # Avoid dense locator clouds at a chapter opening.  The most specific
        # first ten curated matches are enough; later subsections provide
        # additional locators for recurring concepts.
        keys = list(dict.fromkeys(keys))[:10]
        if not keys:
            continue
        commands = "\n".join(f"\\index{{{key}}}" for key in keys)
        payload = f"\n{BEGIN}\n{commands}\n{END}"
        additions.append((insertion_point(text, heading_end, block_end), payload))
        total += len(keys)

    for position, payload in reversed(additions):
        text = text[:position] + payload + text[position:]
    if text != original:
        path.write_text(text, encoding="utf-8")
    return total


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    glossary = root / "chapters/backmatter/glossary.tex"
    glossary_text = glossary.read_text(encoding="utf-8")
    glossary_new = DIRECT_INDEX.sub("", glossary_text)
    if glossary_new != glossary_text:
        glossary.write_text(glossary_new, encoding="utf-8")

    main_text = (root / "main.tex").read_text(encoding="utf-8")
    paths: list[Path] = []
    for name in re.findall(r"\\input\{([^}]+)\}", main_text):
        path = root / f"{name}.tex"
        if not path.exists():
            continue
        if any(part in {"backmatter", "problems"} for part in path.parts):
            continue
        if "appendices" in path.parts:
            # Appendices use hand-placed locators at exact calculation steps.
            # Remove any generated blocks left by an older run, but do not
            # add section-level duplicates.
            original = path.read_text(encoding="utf-8")
            revised = GENERATED.sub("", original)
            if revised != original:
                path.write_text(revised, encoding="utf-8")
            continue
        paths.append(path)

    total = 0
    for path in paths:
        count = rebuild_file(path)
        if count:
            print(f"{path.relative_to(root)}: {count}")
        total += count
    print(f"generated_locators={total}")


if __name__ == "__main__":
    main()
