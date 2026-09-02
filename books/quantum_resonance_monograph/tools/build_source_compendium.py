#!/usr/bin/env python3
"""Build the source-paper technical compendium used by main.tex.

The seven source papers are retained separately under ``arxiv_sources``.  This
script extracts their technical sections, shifts the section hierarchy so that
each paper becomes one dossier in the review appendix, prefixes every internal
label, and copies the associated graphics into the review tree.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Dossier:
    slug: str
    arxiv: str
    source_name: str
    ranges: tuple[tuple[int, int], ...]
    title: str
    citation: str
    guide: str


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
SOURCES = WORKSPACE / "arxiv_sources"
OUT = PROJECT / "source_compendium"
FIGURES = OUT / "figures"


DOSSIERS = (
    Dossier(
        "2503_18741",
        "2503.18741",
        "ewkb_res.tex",
        ((89, 836),),
        "Calculation laboratory I: From a Stokes graph to a resonance width",
        "Morikawa:2025grx",
        "Scattering poles, the cubic oscillator, and the complete inverted "
        "Rosen--Morse calculation, including its repeated Stokes geometry.",
    ),
    Dossier(
        "2505_02301",
        "2505.02301",
        "ewkb_csm-zel.tex",
        ((44, 898),),
        "Calculation laboratory II: One Gamow pole in three realizations",
        "Morikawa:2025xjq",
        "Generalized Riccati equations, Borel summation, Gaussian "
        "regularization, analytic dilation, and the rigged-Hilbert-space "
        "interpretation in one explicit model.",
    ),
    Dossier(
        "2508_09211",
        "2508.09211",
        "ewkb_scattering.tex",
        ((55, 666),),
        "Calculation laboratory III: Transmission, the ABC mechanism, and the continuum",
        "Morikawa:2025vvs",
        "Exact-WKB transmission coefficients, the ABC/Feshbach equivalence, "
        "and the organization of bound, continuum, and resonant sectors.",
    ),
    Dossier(
        "2510_11766",
        "2510.11766",
        "ewkb_radial.tex",
        ((112, 810), (846, 1115)),
        "Calculation laboratory IV: Radial monodromy from oscillator to Coulomb",
        "Morikawa:2025ezl",
        "The radial Riccati problem, oscillator and Coulomb benchmarks, the "
        "exponential map, optimized perturbation theory, anharmonic and "
        "Cornell/Yukawa examples, and the open-path/closed-cycle theorem.",
    ),
    Dossier(
        "2512_24528",
        "2512.24528",
        "csm_berry.tex",
        ((123, 711), (760, 843)),
        "Calculation laboratory V: Encircling an exceptional resonance",
        "Morikawa:2025inx",
        "The complex-scaled Rosen--Morse eigenfunctions, self-orthogonality, "
        "branch exchange, geometric phase, Chern data, monodromy "
        "renormalization, and momentum-bin continuum states.",
    ),
    Dossier(
        "2604_20442",
        "2604.20442",
        "csm_qnm.tex",
        ((172, 1590), (1650, 2083)),
        "Calculation laboratory VI: Schwarzschild and extremal Reissner--Nordstrom QNMs",
        "Ogawa:2026veu",
        "The Regge--Wheeler/Zerilli--Moncrief reduction, complex-scaled basis "
        "construction, matrix elements, stability tests, numerical spectra, "
        "Leaver benchmarks, continuum density, and complex-range Gaussians.",
    ),
    Dossier(
        "2605_03277",
        "2605.03277",
        "csm_qnm_dS.tex",
        ((188, 1281), (1392, 1576)),
        "Calculation laboratory VII: Two-horizon spectra and continuum response",
        "Ogawa:2026dSCSM",
        "Two-horizon complex scaling, QNM and continuum-level-density data, "
        "greybody response, coupled string-inspired channels, higher "
        "dimensions, and block-balancing diagnostics.",
    ),
)


PREREQUISITES = {
    "2503_18741": (
        "Asymptotic scattering coefficients, the Riccati recursion, lateral "
        "Borel sums, simple-turning-point connection matrices, and the "
        "no-incoming-wave condition."
    ),
    "2505_02301": (
        "The resonance connection coefficient, analytic continuation of a "
        "Gamow solution, Gaussian regularization, and analytic dilation."
    ),
    "2508_09211": (
        "The exact-WKB transfer matrix, resolvent boundary values, the ABC "
        "rotation of the continuum, and direct-integral spectral language."
    ),
    "2510_11766": (
        "Exact WKB on a regular contour, Frobenius indices at the origin, "
        "closed-cycle periods, and the Langer transformation."
    ),
    "2512_24528": (
        "Complex-scaled left and right eigenvectors, a second-order "
        "exceptional point, Jordan chains, and Berry holonomy."
    ),
    "2604_20442": (
        "The Regge--Wheeler/Zerilli reduction, QNM boundary conditions, "
        "analytic dilation of the tortoise coordinate, and basis stability."
    ),
    "2605_03277": (
        "Two-horizon boundary conditions, black-hole complex scaling, "
        "continuum level density, and coupled-channel diagonalization."
    ),
}


OUTCOMES = {
    "2503_18741": (
        "Reproduce the inverted Rosen--Morse pole condition and decay width "
        "from the ordered Stokes data and verify them against the exact solution."
    ),
    "2505_02301": (
        "Show on the same solvable model that Zel'dovich, complex-scaled, and "
        "rigged-space pairings encode the same continued resonance datum."
    ),
    "2508_09211": (
        "Compute transmission and continuum/resonance contributions and "
        "identify the analytic statement behind the rotated ABC spectrum."
    ),
    "2510_11766": (
        "Derive radial quantization from both open paths and closed cycles, "
        "then reproduce the oscillator, Coulomb, Cornell, and Yukawa checks."
    ),
    "2512_24528": (
        "Track the branch exchange, self-orthogonality, and geometric phase "
        "through an EP while separating bin normalization from the holonomy."
    ),
    "2604_20442": (
        "Construct the complex-scaled black-hole matrix problem, identify "
        "stable QNMs, and reproduce the Schwarzschild and extremal-RN benchmarks."
    ),
    "2605_03277": (
        "Compute two-horizon QNMs and continuum response, then diagnose "
        "coupled-channel and block-balancing effects."
    ),
}


CHECKPOINTS = {
    "2503_18741": (
        "Recompute the ordered product of Stokes matrices and identify the "
        "entry that multiplies the prohibited incoming branch.",
        "Derive the resonance condition both from the exact hypergeometric "
        "solution and from the exact-WKB connection coefficient.",
        "Change the continuation path or lateral Borel side and record how "
        "the sheet label changes while the physical pole remains consistent.",
    ),
    "2505_02301": (
        "Carry the Gaussian regulator through the Gamow bilinear norm before "
        "taking its analytically continued zero-regulator value.",
        "Rotate the integration contour within the admissible wedge and check "
        "that the exposed pole and residue do not depend on the rotation angle.",
        "Write the same result as a pairing with a test function and identify "
        "the continuity property required of the test-space topology.",
    ),
    "2508_09211": (
        "Extract the transmission denominator from the exact-WKB transfer "
        "matrix and locate its pole on the declared sheet.",
        "Track a sample continuum eigenvalue and a resonance while changing "
        "the complex-scaling angle; only the former should follow the ray.",
        "Reconstruct the continuum level density from the resolvent trace and "
        "separate one pole contribution from the nonresonant background.",
    ),
    "2510_11766": (
        "Derive the Langer term directly from the exponential coordinate map "
        "rather than inserting it as a remembered replacement rule.",
        "Recover the oscillator and Coulomb quantization conditions from both "
        "open-path matching and closed-cycle monodromy.",
        "Vary the auxiliary deformation or optimization parameter and impose "
        "monodromy independence before treating the Cornell or Yukawa case.",
    ),
    "2512_24528": (
        "Expand the resonance condition to second order at the EP and derive "
        "the square-root branches and the associated Jordan vector.",
        "Verify self-orthogonality with the complex-symmetric bilinear product "
        "and relate it to the derivative of the pole condition.",
        "Repeat the encircling calculation at two momentum-bin widths and "
        "separate the bin-dependent norm from the limiting holonomy.",
    ),
    "2604_20442": (
        "Derive the Regge--Wheeler potential from the odd-parity perturbation "
        "equations, including the tortoise-coordinate boundary conditions.",
        "Assemble one finite complex-scaled basis matrix and scan scaling "
        "angle, basis size, and radial range to identify a stable QNM.",
        "Compare the extracted frequency with a Leaver benchmark and inspect "
        "the corresponding continuum-level-density contribution.",
    ),
    "2605_03277": (
        "Derive the local ingoing/outgoing exponents at both horizons and "
        "translate them into admissible complex-deformation wedges.",
        "Reproduce one de Sitter QNM spectrum together with its continuum "
        "level density while varying the cosmological parameter.",
        "For a coupled example, monitor the norms of every matrix block and "
        "demonstrate the effect of block balancing on the stable poles.",
    ),
}


def extract_lines(path: Path, ranges: tuple[tuple[int, int], ...]) -> str:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    chunks = []
    for start, end in ranges:
        chunks.append("".join(lines[start - 1 : end]))
    return "\n".join(chunks)


def prefix_cross_references(text: str, prefix: str) -> str:
    commands = ("label", "ref", "eqref", "pageref", "autoref")
    for command in commands:
        pattern = re.compile(r"\\" + command + r"\{([^{}]+)\}")
        text = pattern.sub(
            lambda match: "\\" + command + "{" + prefix + match.group(1) + "}",
            text,
        )
    return text


def shift_section_hierarchy(text: str) -> str:
    replacements = (
        (r"^(\s*)\\paragraph(\*?)", r"\1\\subparagraph\2"),
        (r"^(\s*)\\subsubsection(\*?)", r"\1\\paragraph\2"),
        (r"^(\s*)\\subsection(\*?)", r"\1\\subsubsection\2"),
        (r"^(\s*)\\section(\*?)", r"\1\\subsection\2"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    return text


def rewrite_graphics(text: str, dossier: Dossier) -> str:
    prefix = f"source_compendium/figures/{dossier.slug}/"

    def replace(match: re.Match[str]) -> str:
        path = match.group(2)
        if path.startswith("/"):
            return match.group(0)
        path = path.replace("ene_exRn", "ene_exRN")
        if dossier.slug == "2604_20442" and path == "fig/lev-th10-20.eps":
            path = "fig/lev-th10-20-eps-converted-to.pdf"
        return match.group(1) + prefix + path + match.group(3)

    pattern = re.compile(r"(\\includegraphics(?:\[[^\]]*\])?\{)([^{}]+)(\})")
    text = pattern.sub(replace, text)
    text = text.replace("1.25\\columnwidth", "0.95\\linewidth")
    text = text.replace("\\begin{figure*}", "\\begin{figure}")
    text = text.replace("\\end{figure*}", "\\end{figure}")
    return text


def deduplicate_active_labels(text: str) -> str:
    """Drop repeated non-comment labels while preserving commented source."""
    seen: set[str] = set()
    output: list[str] = []
    pattern = re.compile(r"\\label\{([^{}]+)\}")
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("%"):
            output.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            label = match.group(1)
            if label in seen:
                return ""
            seen.add(label)
            return match.group(0)

        line = pattern.sub(replace, line)
        if not line.strip():
            continue
        output.append(line)
    return "".join(output)


def resize_selected_tikz(text: str, dossier: Dossier) -> str:
    """Fit source figures whose original multi-panel canvas exceeds one column."""
    labels: tuple[str, ...] = ()
    if dossier.slug == "2508_09211":
        labels = ("src:2508_09211:fig:stokes_dist",)
    elif dossier.slug == "2604_20442":
        labels = (
            "src:2604_20442:fig:exRN_scalar_QNM",
            "src:2604_20442:fig:exRN_em_QNM",
            "src:2604_20442:fig:exRN_grav_QNM",
        )

    figure_pattern = re.compile(
        r"\\begin\{figure\}(?:\[[^\]]*\])?.*?\\end\{figure\}",
        flags=re.DOTALL,
    )

    def fit(match: re.Match[str]) -> str:
        figure = match.group(0)
        if not any(f"\\label{{{label}}}" in figure for label in labels):
            return figure
        figure = figure.replace(
            "\\begin{tikzpicture}",
            "\\resizebox{\\linewidth}{!}{%\n\\begin{tikzpicture}",
            1,
        )
        figure = figure.replace(
            "\\end{tikzpicture}",
            "\\end{tikzpicture}%\n}",
            1,
        )
        return figure

    return figure_pattern.sub(fit, text)


def transform(dossier: Dossier) -> str:
    source_dir = SOURCES / dossier.arxiv
    source_path = source_dir / dossier.source_name
    text = extract_lines(source_path, dossier.ranges)
    text = shift_section_hierarchy(text)
    text = prefix_cross_references(text, f"src:{dossier.slug}:")
    text = rewrite_graphics(text, dossier)
    text = resize_selected_tikz(text, dossier)
    text = deduplicate_active_labels(text)
    text = text.replace("\\emph{", "\\textit{")
    text = text.replace(
        "Open-path $\\Leftrightarrow$ Closed-cycle: a general statement",
        "Open-path and closed-cycle equivalence: a general statement",
    )
    text = text.replace(
        "Analyticity of~$\\lambda$ near resonance pole",
        "Analyticity of the control parameter near the resonance pole",
    )
    text = text.replace("Appendix~\\ref{src:", "Sec.~\\ref{src:")
    text = text.replace("In this Appendix,", "In this calculation module,")
    text = text.replace("In this \\revtwo{Appendix},", "In this \\revtwo{calculation module},")
    text = text.replace(
        "Thus, the main message of this Appendix is simple:",
        "Thus, the main message of this calculation module is simple:",
    )
    text = text.replace(
        "In contrast, in Appendices we consider nonintegrable examples",
        "In contrast, in the later nonintegrable examples we consider",
    )
    if dossier.slug == "2605_03277":
        text = text.replace(
            "\\subsubsection{Coupled-channel systems: toward stringy black holes}",
            "\\enlargethispage{4pt}\n"
            "\\subsubsection{Coupled-channel systems: toward stringy black holes}",
        )
    if dossier.slug == "2508_09211":
        text = text.replace(
            "x=0.6mm,y=0.6mm,>=latex",
            "x=0.58mm,y=0.58mm,>=latex",
        )
        text = text.replace(
            "\\end{enumerate}\nThe resonant state at a finite $\\theta$",
            "\\end{enumerate}\n\\clearpage\n"
            "The resonant state at a finite $\\theta$",
            1,
        )

    header = f"""% Generated from arXiv:{dossier.arxiv}; see tools/build_source_compendium.py.
\\section{{{dossier.title}}}
\\label{{lab:{dossier.slug}}}

\\calculationroute
  {{{PREREQUISITES[dossier.slug]}}}
  {{{dossier.guide}}}
  {{{OUTCOMES[dossier.slug]}}}

The detailed derivation follows Ref.~\\cite{{{dossier.citation}}} and is
retained essentially in full so that the calculation can be repeated line by
line.  Notation local to the source paper is reintroduced where it first
appears.  Internal labels are namespaced, while the original bibliography keys
and the original TikZ construction are preserved.

"""
    checkpoint_items = "\n".join(
        f"  \\item {item}" for item in CHECKPOINTS[dossier.slug]
    )
    footer = f"""

\\subsection*{{Laboratory checkpoint}}
Before moving to the next stage, perform the following checks without copying
the displayed final answer.
\\begin{{enumerate}}
{checkpoint_items}
\\end{{enumerate}}
"""
    return header + text.rstrip() + footer


def copy_assets(dossier: Dossier) -> None:
    source_dir = SOURCES / dossier.arxiv
    destination = FIGURES / dossier.slug
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".pdf", ".eps", ".png"}:
            target = destination / path.relative_to(source_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def write_master() -> None:
    rows = "\n".join(
        f"arXiv:{d.arxiv} & {d.title} & Sec.~\\ref{{lab:{d.slug}}} \\\\"
        for d in DOSSIERS
    )
    inputs = "\n".join(
        f"\\input{{source_compendium/dossier_{d.slug}}}" for d in DOSSIERS
    )
    master = f"""% Generated by tools/build_source_compendium.py.
\\section{{Calculation laboratories: inventory}}
\\label{{sec:calculation-laboratory-inventory}}

The preceding chapters develop a single conceptual line from scattering
theory to black-hole quasinormal modes.  The present compendium supplies the
long calculations behind that line.  It deliberately retains intermediate
steps, alternative parameterizations, solvable-model checks, numerical tables,
and the original TikZ diagrams from the authors' papers.  Some ideas therefore
appear more than once: the first occurrence teaches the common structure,
whereas the dossier occurrence shows the complete calculation in the notation
in which it was originally obtained.

\\begin{{longtable}}{{@{{}}p{{0.20\\linewidth}}p{{0.51\\linewidth}}p{{0.21\\linewidth}}@{{}}}}
\\toprule
source & detailed subject & location \\\\
\\midrule
\\endfirsthead
\\toprule
source & detailed subject & location \\\\
\\midrule
\\endhead
{rows}
\\bottomrule
\\end{{longtable}}

{inputs}
"""
    (OUT / "technical_compendium.tex").write_text(master, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for dossier in DOSSIERS:
        copy_assets(dossier)
        output_path = OUT / f"dossier_{dossier.slug}.tex"
        output_path.write_text(transform(dossier), encoding="utf-8")


if __name__ == "__main__":
    main()
