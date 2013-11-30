##
## Makefile
##  
## Made by Miguel Angel Garcia
## Login   <migueltormenta>
##
## Started on  Fri Jan  8 20:54:19 2010 Miguel Angel Garcia
## Last update Fri Jan  8 20:54:19 2010 Miguel Angel Garcia
## 

GLADE:=$(wildcard ../glade/*.glade)
PY:=$(wildcard ../*.py)
PO:=$(wildcard *.po)
POT:=$(wildcard *.pot)
MO:=$(PO:.po=/LC_MESSAGES/pygrep.mo)


.PHONY : all
all : $(MO)

messages.pot : $(PY)
	pygettext -o $@ $^
	xgettext -j -o $@ $(GLADE)

%.po : messages.pot
	msgmerge -U $@ messages.pot

es/LC_MESSAGES/pygrep.mo : es.po
	mkdir -p es/LC_MESSAGES
	msgfmt $< -o $@

en/LC_MESSAGES/pygrep.mo : en.po
	mkdir -p en/LC_MESSAGES
	msgfmt $< -o $@


.PHONY : clean
clean :
	$(RM) $(POT) $(MO) *~
