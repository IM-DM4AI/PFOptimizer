# define and add dynamic context ruses rules
from dycacher.import_hook import capture_arguments 
from dycacher.import_hook import when_imported, wrap_onnx_config_class

@when_imported('pickle')
def rule_pickle(mod):
    mod.load = capture_arguments(mod.load)

@when_imported('joblib')
def rule_joblib(mod):
    mod.load = capture_arguments(mod.load)

@when_imported('onnxruntime')
def rule_ort(mod):
    mod.InferenceSession = capture_arguments(mod.InferenceSession)
    mod.SessionOptions = wrap_onnx_config_class(mod.SessionOptions)

@when_imported('xgboost')
def rule_xgboost(mod):
    pass

@when_imported('lightgbm')
def rule_lightgbm(mod):
    mod.Booster = capture_arguments(mod.Booster)
 