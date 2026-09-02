MAIN = main
INDEX_DIC = bhindex.dic

.PHONY: all clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex chapters/*.tex ref.bib omphys.sty natbib.sty utphys.bst $(INDEX_DIC)
	uplatex -interaction=nonstopmode -halt-on-error $(MAIN).tex
	pbibtex $(MAIN)
	mendex -U -d $(INDEX_DIC) $(MAIN).idx
	uplatex -interaction=nonstopmode -halt-on-error $(MAIN).tex
	uplatex -interaction=nonstopmode -halt-on-error $(MAIN).tex
	dvipdfmx -o $(MAIN).pdf $(MAIN).dvi

clean:
	-rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).dvi
	-rm -f $(MAIN).fdb_latexmk $(MAIN).fls $(MAIN).log $(MAIN).out $(MAIN).toc
	-rm -f $(MAIN).idx $(MAIN).ind $(MAIN).ilg
