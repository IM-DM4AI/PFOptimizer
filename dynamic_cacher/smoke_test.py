import dycacher

def predict(*args):
    import pickle
    import numpy as np
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    scaler_path = '/home/admin0/PFRewriter/dynamic_cacher/models/expedia_standard_scale_model.pkl'
    enc_path = '/home/admin0/PFRewriter/dynamic_cacher/models/expedia_one_hot_encoder.pkl'
    model_path = '/home/admin0/PFRewriter/dynamic_cacher/models/expedia_lr_model.pkl'
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    with open(enc_path, 'rb') as f:
        enc = pickle.load(f)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    # data = np.column_stack(args)
    # data = np.split(data, np.array([8]), axis = 1)
    # numerical = data[0]
    # categorical = data[1]
    # X = np.hstack((scaler.transform(numerical), enc.transform(categorical).toarray()))
    # return model.predict(X)

import time

if __name__ == "__main__":
    start = time.perf_counter()
    for i in range(10000):
        predict()

    end = time.perf_counter()

    print((end-start)*1000, "ms")