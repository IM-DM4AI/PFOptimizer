import sys
from dycacher.import_hook import PostImportFinder, reset_cache, write_to_shm, load_from_shm, close_shm, try_to_load_cache
from dycacher.api_rules import *

# add import hook while importing this module
sys.meta_path.insert(0, PostImportFinder())

__all__ = ["reset_cache"]