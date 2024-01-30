import math
import numpy as np
import pandas as pd

def timeEncoder(X):
    X_hm = X["time"].str.split(":", expand=True)
    d = pd.to_datetime(
        dict(
            year=X["year"],
            month=X["month"],
            day=X["day"],
            hour=X_hm[0],
            minute=X_hm[1],
        )
    ).astype(int)
    return pd.DataFrame(d)

def amtEncoder(X):
    amt = (
        X.apply(lambda x: x[1:])
        .astype(float)
        .map(lambda amt: max(1, amt))
        .map(math.log)
    )
    return pd.DataFrame(amt)

def decimalEncoder(X, length=5):
    dnew = pd.DataFrame()
    for i in range(length):
        dnew[i] = np.mod(X, 10)
        X = np.floor_divide(X, 10)
    return dnew

def fraudEncoder(X):
    return np.where(X == "Yes", 1, 0).astype(int)