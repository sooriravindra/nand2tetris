#! /bin/bash
for jackfile in $(find . -name "*jack" -type f); do
  xmlfile="${jackfile%.jack}.xml"
  filename=$(basename "$jackfile")
  prsfile="${filename%.jack}.prs"

  ./analyzer.py $jackfile
  ../../tools/TextComparer.sh "${xmlfile}" "${prsfile}"
done
