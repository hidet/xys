import os
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



def save_numpy_arrays(enes,outs,fname):
    # enes: energy range
    # outs: values (quantum efficiency or fluorescence)
    # file check
    fname=file_check(fname)
    # save
    np.savetxt(fname, np.transpose([enes,outs]), delimiter=',', fmt='%1.6e')
    print("%s is created."%fname)


def file_check(f):
    if os.path.exists(f):
        name,ext=os.path.splitext(f)
        i=1
        while True:
            new_name="{}_{:0=3}{}".format(name,i,ext)
            if not os.path.exists(new_name):
                return new_name
            i += 1
    else:
        return f
