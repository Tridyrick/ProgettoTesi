# Script that should be called by __main__.py that creates a temporary container with the given arguments (after pynguin_image)
param (
    [Parameter(Mandatory=$true)][string]$algorithm,
    [Parameter(Mandatory=$true)][string]$project,
    [Parameter(Mandatory=$true)][string]$module,
    [Parameter(Mandatory=$true)][string]$test,
    [Parameter(Mandatory=$false)][string]$reset,
    [Parameter(Mandatory=$false)][string]$report,
    [Parameter(Mandatory=$true)][int]$iteration,
    [Parameter(Mandatory=$true)][string]$python_path
)

$start = "${env:USERPROFILE}/Desktop/uni/tirocinio"

# Using /dev/null as the config file so that pytest doesn't capture the config file of the project
docker run `
--rm `
--gpus 'all,capabilities=utility' `
-v "$start/projects:/input" `
-v "$start/output:/output" `
-v "$start/package:/package" `
-v "$start/energy_measurements:/energy_measurements" `
-v "$start/reports/coverage/${algorithm}/iteration_${iteration}:/reports" `
-v "$start/coverages:/coverages" `
-e PYTHONPATH="$python_path" `
pynguin_image `
"$project" `
-type 'execution' `
"$reset" `
"$report" `
-p no:cacheprovider `
--cov="$module" `
--cov-config='/dev/null' `
--cov-append `
--cov-branch `
--config-file '/dev/null' `
--rootdir="/input/$project" `
"/input/$project/pynguin_tests/$algorithm/iteration_${iteration}/$test"
