# Makefile

CFLAGS= -std=c99

perfect: list.o divisor.o perfect.o

list.o: list.h
divisor.o: list.h

clean:
	rm -f list.o divisor.o perfect.o perfect

install: perfect
	cp perfect ~/bin
