import sys
from dycacher.import_hook import *

# add import hook while importing this module
sys.meta_path.insert(0, PostImportFinder())

# define and add dynamic context ruses rules
@when_imported('pickle')
def replace_decorate(mod):
    mod.load = capture_arguments(mod.load)
