import dycacher
import os

script_path = os.path.dirname(__file__)

def predict(*args):
    import pickle
    import numpy as np
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    import onnxruntime as ort
    import joblib
    import lightgbm as lgb

    scaler_path = f'{script_path}/models/expedia_standard_scale_model.pkl'
    enc_path = f'{script_path}/models/expedia_one_hot_encoder.pkl'
    model_path = f'{script_path}/models/expedia_lr_model.pkl'
    model_path2 = f'{script_path}/models/uc06.python.model'
    model_path3 = f'{script_path}/models/expedia_dt_pipeline.onnx'
    model_path4 = f'{script_path}/models/creditcard_lgb_model.txt'

    ortconfig = ort.SessionOptions()
    expedia_onnx_session = ort.InferenceSession(model_path3, sess_options=ortconfig)

    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    with open(enc_path, 'rb') as f:
        enc = pickle.load(f)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(model_path2) as f:
        uc06_model = joblib.load(model_path2)

    lgbm_model = lgb.Booster(model_file=model_path4)

import time
if __name__ == "__main__":
    start = time.perf_counter()
    for i in range(100):
        predict()

    end = time.perf_counter()

    dycacher.reset_cache()

    print((end-start)*1000, "ms")