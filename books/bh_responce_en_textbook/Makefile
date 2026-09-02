MAIN = main
BIBTEX := $(shell command -v bibtex 2>/dev/null || command -v bibtex.original 2>/dev/null || printf '%s' bibtex)

.PHONY: all clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex chapters/*.tex ref.bib omphys.sty natbib.sty utphys.bst
	pdflatex -interaction=nonstopmode -halt-on-error $(MAIN).tex
	$(BIBTEX) $(MAIN)
	makeindex $(MAIN).idx
	pdflatex -interaction=nonstopmode -halt-on-error $(MAIN).tex
	pdflatex -interaction=nonstopmode -halt-on-error $(MAIN).tex

clean:
	-rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).dvi $(MAIN).pdf
	-rm -f $(MAIN).fdb_latexmk $(MAIN).fls $(MAIN).log $(MAIN).out $(MAIN).toc
	-rm -f $(MAIN).idx $(MAIN).ind $(MAIN).ilg
