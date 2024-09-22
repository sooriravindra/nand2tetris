BUILDDIR  = build
OSDIR     = os
SOURCEDIR = games
SOURCES := $(shell find $(SOURCEDIR) -name '*.jack')
OSFILES := $(shell find $(OSDIR) -name '*.jack')
HACKFILES := $(BUILDDIR)/Clack.hack $(BUILDDIR)/Pong.hack

.PHONY: all clean check
.SECONDARY:

$(BUILDDIR): $(SOURCES) $(OSFILES)
	mkdir -p 	$@
	cp -r $(SOURCEDIR)/* $@
	ls -1 $@ | xargs -I{} sh -c "cp $(OSFILES) $@/{}"

$(BUILDDIR)/%/Main.vm: $(BUILDDIR)
	./compilers/compiler.py $(dir $@)

$(BUILDDIR)/%.asm: $(BUILDDIR)/%/Main.vm
	./compilers/translator.py $(@:%.asm=%) --optimize deadcode,return,call,cond

$(BUILDDIR)/%.hack: $(BUILDDIR)/%.asm
	./compilers/assembler.py $(@:%.hack=%.asm) > $@

all: $(HACKFILES)

clean:
	rm -rf build

check: clean all
	@echo "#####################"
	@echo "      TEST BEGIN"
	@echo "#####################"
	@wc -l $(HACKFILES)
	@echo "\033[0;31m"
	@wc -l $(HACKFILES) |sed -e "s/^ *\([0-9]*\) .*/\1/" | head -n2 | xargs -I{} bash -c "if [ {} -gt 32768 ]; then echo \"{} --> Program too big!\"; fi"
	@echo "\033[0m"
	@echo "#####################"
	@echo "    TEST COMPLETE"
	@echo "#####################"
