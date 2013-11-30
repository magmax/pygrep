all: pygrep.1 view

pygrep.1:pygrep.xml
	xsltproc -''-nonet -''-param man.charmap.use.subset "0"           -''-param make.year.ranges "1" -''-param make.single.year.ranges "1" /usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl $<

view::
	nroff -man pygrep.1

