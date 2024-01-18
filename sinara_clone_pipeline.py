from subprocess import STDOUT, run, call

run_result = run(f'tsrc init https://github.com/4-DS/dataflow_designer_ml_default.git',
                 shell=True, stderr=STDOUT, cwd=None)
if run_result.returncode !=0 :
    raise Exception(f'Could not clone SinaraML pipeline!')
