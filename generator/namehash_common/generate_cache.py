'''
Executes all functions registered with pickled_property, generating cache.
For each function, creates an instance of the function's class
trying a default constructor first, then using the production config.
'''

import shutil
import os
from hydra import compose, initialize

import generator.xgenerator
# if there are modules not imported by xgenerator, import them here
import generator.namehash_common.ngrams

import generator.namehash_common.pickle_cache as pickle_cache
from generator.namehash_common.paths import PROJECT_ROOT


if __name__ == '__main__':
    # cd to the root of the project
    os.chdir(PROJECT_ROOT)

    with initialize(version_base=None, config_path='../../conf/'):
        config = compose(config_name='prod_config_new')

        print('Removing old cache')
        shutil.rmtree(pickle_cache.CACHE_DIR, ignore_errors=True)

        for module, class_name, func_name in pickle_cache.REGISTERED_FUNCTIONS:
            print(f'Generating {module}{class_name}.{func_name}')
            exec(f'import {module}')
            try:
                # try default constructor
                exec(f'{module}.{class_name}().{func_name}')
            except TypeError:
                # pass config
                exec(f'{module}.{class_name}(config).{func_name}')
