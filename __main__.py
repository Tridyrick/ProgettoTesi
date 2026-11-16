#!/usr/bin/env python3

import subprocess
import pathlib
import os
import pandas as pd

def _createProjectDict(file: os.PathLike) -> dict[str, str]:
    projects = {}
    with file.open('r') as f:
        projects.update(line.split() for line in f)
    return projects

def _setUpProjectDirectory(path: os.Pathlike) -> None:
    path_init = path / '__init__.py'
    if not path.exists():
        path.mkdir()
    path_init.touch()

def _measureGenEnergyConsumption(script: os.PathLike, project: str, module: str, iteration: int, algorithm: str, seed: int) -> None:
    subprocess.run(['powershell',
                    '-File',
                    f'{script}',
                    '-project',
                    f'{project}',
                    '-name',
                    f'{module}',
                    '-algorithm',
                    f'{algorithm}',
                    '-seed',
                    f'{seed}',
                    '-iteration',
                    f'{iteration}'])

def _measureExecEnergyConsumption(script: os.PathLike, project: str, module: str, test: str, python_path: str, iteration: int, algorithm: str, first: bool, last: bool) -> None:
    args = ['powershell',
            '-File',
            f'{script}',
            '-project',
            f'{project}',
            '-module',
            f'{module}',
            '-test',
            f'{test}',
            '-python_path',
            f'{python_path}',
            '-algorithm',
            f'{algorithm}',
            '-iteration',
            f'{iteration}']
    # if the respective flags are true you need to add the optional arguments too...
    if first:
        args += ['-reset', 'reset']
    if last:
        args += ['-report', 'report']
    subprocess.run(args)
    # ...and then remove them
    if last:
        del args[-2:]
    if first:
        del args[-2:]

def _fixEmissionsFile(data_path: os.PathLike, project: str, algorithm: str) -> None:
    project_name = project + '_' + algorithm
    df = pd.read_csv(data_path)
    df.loc[df['project_name'] == 'codecarbon', 'project_name'] = project_name
    df.to_csv(data_path, index=False)

def main() -> None:
    ALGORITHMS = ['DYNAMOSA',
                  'MOSA',
                  'MIO',
                  'WHOLE_SUITE',
                  'RANDOM_TEST_CASE_SEARCH',
                  'RANDOM_TEST_SUITE_SEARCH',
                  'WHOLE_SUITE_ENERGY_AWARE',
                  'MIO_ENERGY_AWARE',
                  'WHOLE_SUITE_ENERGY_AWARE_ALT',
                  'MIO_ENERGY_AWARE_ALT'
                  ]
    PROJECT_ABSOLUTE_PATH = pathlib.Path(__file__).parent
    FILE_WITH_PROJECTS = PROJECT_ABSOLUTE_PATH / 'projects_modules.txt'
    # the seeds found in this file were generated using urandom
    FILE_WITH_SEEDS = PROJECT_ABSOLUTE_PATH / 'projects_seeds.txt'
    gen_data_path = PROJECT_ABSOLUTE_PATH / 'energy_measurements' / 'test_gen_energy_measurements.csv'
    exec_data_path = PROJECT_ABSOLUTE_PATH / 'energy_measurements' / 'test_exec_energy_measurements.csv'
    PROJECTS = {project: pathlib.Path(path) for project, path in _createProjectDict(FILE_WITH_PROJECTS).items()}
    ITERATIONS = 3
    SEEDS = {key: int(value) for key, value in _createProjectDict(FILE_WITH_SEEDS).items()}

    print('Creating pynguin test folders for each project...')
    for project in PROJECTS:
        project_test_path = PROJECT_ABSOLUTE_PATH / 'projects' / project / 'pynguin_tests'
        _setUpProjectDirectory(project_test_path)
        for algorithm in ALGORITHMS:
            project_test_path /= algorithm
            _setUpProjectDirectory(project_test_path)
            for i in range(1,ITERATIONS+1):
                project_test_path /= f'iteration_{i}'
                _setUpProjectDirectory(project_test_path)
                project_test_path = project_test_path.parent
            project_test_path = project_test_path.parent
    print('Done!')
    print()

    print('Creating coverage folders for each algorithm...')
    for algorithm in ALGORITHMS:
        coverage_path = PROJECT_ABSOLUTE_PATH / 'reports' / 'coverage' / algorithm
        if not coverage_path.exists():
            coverage_path.mkdir()
        for i in range(1,ITERATIONS+1):
            coverage_path /= f'iteration_{i}'
            if not coverage_path.exists():
                coverage_path.mkdir()
            coverage_path = coverage_path.parent
    print('Done!')
    print()

    script_path = PROJECT_ABSOLUTE_PATH / 'docker_gen_config.ps1'
    print(f'Checking if {gen_data_path} exists...')
    if not gen_data_path.exists():
        print('Starting measurement of energy consumption of test generation...')
        # cycle that runs all modules in all algorithms, will take A LOT!
        for project, module in PROJECTS.items():
            for algorithm in ALGORITHMS:
                for iteration in range(1, ITERATIONS+1):
                    _measureGenEnergyConsumption(script_path, project, module, iteration, algorithm, SEEDS[project])
                    _fixEmissionsFile(gen_data_path, project, algorithm)
    print('Completed measurements!')
    print()

    script_path = PROJECT_ABSOLUTE_PATH / 'docker_exec_config.ps1'
    print(f'Checking if {exec_data_path} exists...')

    FILE_WITH_PATHS = PROJECT_ABSOLUTE_PATH / 'projects_paths.txt'
    PYTHON_PATHS = _createProjectDict(FILE_WITH_PATHS)
    LEN_PROJECTS = len(PROJECTS)

    if not exec_data_path.exists():
        print('Starting measurement of energy consumption of test execution...')
        for iteration in range(1,ITERATIONS+1):
            # for every algorithm it needs to generate a report and so needs to track which is the first and last project (for reset .coverage and report)
            for algorithm in ALGORITHMS:
                project_counter = 0
                for project, module in PROJECTS.items():
                    project_test_path = PROJECT_ABSOLUTE_PATH / 'projects' / project / 'pynguin_tests' / algorithm / f'iteration_{iteration}'
                    for test in project_test_path.glob('*.py'):
                        if test.name != '__init__.py':
                            _measureExecEnergyConsumption(script_path, project, module, test.name, PYTHON_PATHS[project], iteration, algorithm, project_counter == 0, project_counter == LEN_PROJECTS-1)
                            _fixEmissionsFile(exec_data_path, project, algorithm)
                    project_counter += 1

    for iteration in range(1,ITERATIONS+1):
        for algorithm in ALGORITHMS[-2:]:
            project_counter = 0
            for project, module in PROJECTS.items():
                project_test_path = PROJECT_ABSOLUTE_PATH / 'projects' / project / 'pynguin_tests' / algorithm / f'iteration_{iteration}'
                for test in project_test_path.glob('*.py'):
                    if test.name != '__init__.py':
                        _measureExecEnergyConsumption(script_path, project, module, test.name, PYTHON_PATHS[project], iteration, algorithm, project_counter == 0, project_counter == LEN_PROJECTS-1)
                        _fixEmissionsFile(exec_data_path, project, algorithm)
                project_counter += 1

    print('Completed measurements!')
    print()

if __name__ == '__main__':
    main()
