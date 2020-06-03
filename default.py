import pandas as pd
import numpy as np


def read_default_csv(fname):
    df = pd.read_csv(fname)
    dic=df.set_index('ID').T.to_dict('list')
    keys=[*dic.keys()]
    for key in keys:
        delinds=[]
        for i,el in enumerate(dic[key]):
            try:
                if np.isnan(float(el)): delinds.append(i)
            except:
                print(key,el)
        for ind in delinds: del dic[key][delinds[0]]
    return dic



