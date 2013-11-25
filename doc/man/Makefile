all: pycardsyncer.1 pc_query.1 pycard-import.1

# view with
# nroff -e -mandoc pycardsyncer.1 | less
pycardsyncer.1: pycardsyncer.txt
	a2x -f manpage pycardsyncer.txt

pc_query.1: pc_query.txt
	a2x -f manpage pc_query.txt

pycard-import.1: pycard-import.txt
	a2x -f manpage pycard-import.txt
