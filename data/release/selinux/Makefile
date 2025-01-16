# Taken and updated from https://github.com/freeipa/freeipa/blob/release-4-12-2/selinux/Makefile.am
SELINUXTYPE = targeted
NULL =

MODULE = clad.pp.bz2
MODULE_IF = clad.if

dist_noinst_DATA =	\
	clad.fc			\
	clad.if			\
	clad.te			\
	$(NULL)

selinuxpolicydir = $(datarootdir)/selinux/packages/$(SELINUXTYPE)
nodist_selinuxpolicy_DATA =	\
	$(MODULE)				\
	$(NULL)

selinux_makefile = /usr/share/selinux/devel/Makefile

%.pp.bz2: %.pp
	bzip2 -f -9 $^

%.pp: %.te %.fc %.if
	make -f $(selinux_makefile) $@

clean-local:
	rm -rf *~  *.tc *.pp *.pp.bz2 tmp *.cil

test:
	# https://access.redhat.com/articles/6999267
	sudo semodule -i clad.pp

%.cil: %.pp
	cat clad.pp | /usr/libexec/selinux/hll/pp > clad.cil
