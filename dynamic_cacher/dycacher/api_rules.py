# define and add dynamic context ruses rules
import types
from dycacher.import_hook import reuse_checking, decorate_instance_method
from dycacher.import_hook import when_imported, wrap_onnx_config_class

@when_imported('pickle')
def rule_pickle(mod):
    mod.load = reuse_checking(mod.load)

@when_imported('joblib')
def rule_joblib(mod):
    mod.load = reuse_checking(mod.load)

@when_imported('onnxruntime')
def rule_ort(mod):
    mod.InferenceSession = reuse_checking(mod.InferenceSession)
    mod.SessionOptions = wrap_onnx_config_class(mod.SessionOptions)

@when_imported('xgboost')
def rule_xgboost(mod):
    mod.Booster = decorate_instance_method(mod.Booster, "load_model", reuse_checking)
    mod.Booster = reuse_checking(mod.Booster)

@when_imported('lightgbm')
def rule_lightgbm(mod):
    mod.Booster = reuse_checking(mod.Booster)

@when_imported('tensorflow')
def rule_tensorflow(mod):
    mod.keras.models.load_model = reuse_checking(mod.keras.models.load_model)

@when_imported('torch')
def rule_torch(mod):
    mod.load = reuse_checking(mod.load)
 