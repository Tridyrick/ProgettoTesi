#!/usr/bin/env bash

# measures the energy consumption based on the type of operation (either test generation with pynguin or test execution with pytest)

# assume that the type argument is in the first two arguments
type="$2"
shift 2
found_reset=1
found_report=1
COVERAGE_FILE_PATH='/coverages/.coverage'

FILE_IN='/pynguin/emissions.csv'
# the out file depends on the type of operation you want to measure

case "$type" in
    'generation')
        file_out='/energy_measurements/test_gen_energy_measurements.csv'
        command=('pynguin')
    ;;

    'execution')
        file_out='/energy_measurements/test_exec_energy_measurements.csv'
        command=('pytest')
        if [ "$1" = 'reset' ]; then
            found_reset=0
            shift
        fi

        if [ "$1" = 'report' ]; then
            found_report=0
            shift
        fi
    ;;

    *)
        echo "$type is not a valid type."
        exit 1
    ;;
esac

# if specified a reset, then erase the remaining coverage file
if [ "$type" = 'execution' -a "$found_reset" -eq 0 ]; then
    coverage erase --data-file="$COVERAGE_FILE_PATH" --rcfile=''
fi
# execute the measurements
codecarbon monitor --offline --country-iso-code ITA --region 'friuli venezia giulia' -- "${command[@]}" "$@"
# if specified a report, combines the results obtained at the end
if [ "$type" = 'execution' ]; then
    mv '/pynguin/.coverage' "$COVERAGE_FILE_PATH.$(date +%Y%m%d_%H%M%S)"
    if [ "$found_report" -eq 0 ]; then
        coverage combine --data-file="$COVERAGE_FILE_PATH" -q --rcfile='' '/coverages' && coverage json --rcfile='' -q -i --data-file="$COVERAGE_FILE_PATH" -o '/reports/cov_report.json'
    fi
fi

if [ ! -f "$file_out" ]; then
    cp "$FILE_IN" "$file_out"
else
    # ignores the header and appends the rest of the measurements in the out file
    sed '1d' "$FILE_IN" >> "$file_out"
fi
