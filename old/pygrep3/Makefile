

all:

doc:
	xgettext -c -j -p po --force-po *.py glade/pygrep.glade
	@echo Command to initialize a language:
	@echo msginit -i messages.po -o es.po

clean:
	$(RM) *.pyc
	make -C po clean