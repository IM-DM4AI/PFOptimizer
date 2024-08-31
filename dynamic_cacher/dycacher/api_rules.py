# define and add dynamic context ruses rules
from dycacher.import_hook import capture_arguments, when_imported

@when_imported('pickle')
def replace_decorate(mod):
    mod.load = capture_arguments(mod.load)