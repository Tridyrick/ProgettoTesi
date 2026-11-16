# Script that should be called by __main__.py that creates a temporary container with the given arguments (after pynguin_image)
param (
    [Parameter(Mandatory=$true)][string]$name,
    [Parameter(Mandatory=$true)][string]$algorithm,
    [Parameter(Mandatory=$true)][string]$project,
    [Parameter(Mandatory=$true)][int]$seed,
    [Parameter(Mandatory=$true)][int]$iteration
)

$start = "${env:USERPROFILE}/Desktop/uni/tirocinio"
$projects = "$start/projects"
$project_path = "$projects/$project"
$tests_path = "$project_path/pynguin_tests/$algorithm/iteration_${iteration}"
$project_name = "${project}_$algorithm"

# In case any energy aware algorithm is found, the energy metric needs to be turned on for that algorithm
$energy = ''
if ("$algorithm" -cmatch '\w+_ENERGY_AWARE') {
    $algorithm = "$algorithm" -creplace '_ENERGY_AWARE.*', ''
    $energy = 'ENERGY'
}

docker run `
--rm `
--gpus 'all,capabilities=utility' `
-v "${projects}:/input" `
-v "$start/output:/output" `
-v "$start/package:/package" `
-v "${tests_path}:/tests" `
-v "$start/reports/pynguin:/reports" `
-v "$start/log:/log" `
-v "$start/energy_measurements:/energy_measurements" `
pynguin_image `
"$project" `
-type 'generation' `
--project-path "/input/$project" `
--output-path '/tests' `
--statistics-backend CSV `
--project-name "$project_name" `
--report-dir '/reports' `
--output-variable ProjectName TargetModule SearchTime TotalTime BranchCoverage Coverage RandomSeed AlgorithmIterations Goals MutationScore Fitness `
--seed "$seed" `
--coverage-metrics BRANCH "$energy" `
--maximum-search-time -1 `
--maximum-memory -1 `
--maximum-iterations 1000 `
--log-file '/log/pynguin_log.log' `
--module-name "$name" `
--algorithm "$algorithm"
