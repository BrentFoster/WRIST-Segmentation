from math import sqrt
print([sqrt(i ** 2) for i in range(100000000)])


from joblib import Parallel, delayed
print('Done!')
print(Parallel(n_jobs=2)(delayed(sqrt)(i ** 2) for i in range(100000000)))