from math import sqrt
from joblib import Parallel, delayed
import sys

import timeit
import time

import json
import numpy as np
import sys

# subprocess.check_output("python C:\Users\Brent\GitRepositories\BoneSegmentation\SlicerModule\joblib_test.py")

def main(x):


	print('huehue')

	# x = ''.join(x)
	print(x)
	print(type(x))

	# print(np.array_str(np.arange(3)))

	print(np.array(json.loads(x)))


	print('done!!')

	start_time = timeit.default_timer()

	# with Parallel(n_jobs=-1, verbose=5) as parallel:
	# 	accumulator = 0.
	# 	n_iter = 0
	# 	while accumulator < 5:
	# 		results = parallel(delayed(main)(accumulator + i ** 2) for i in range(10))
	# 		accumulator += sum(results)  # synchronization barrier
	# 		n_iter += 1
			
	print('done!!')


	# print(accumulator, n_iter)     
	print(timeit.default_timer() - start_time, 'seconds') 



	return 14


if __name__ == '__main__':

	start_time = timeit.default_timer()

	print('huehue')
	# x = sys.argv[1:len(sys.argv)]

	# import numpy as np

	# x = ''.join(x)



	import os
	print(os.path.dirname(os.path.abspath(__file__)))
	print(os.getcwd())

	print(timeit.default_timer() - start_time, 'seconds') 

	# print(np.array_str(np.arange(3)))

	# print(np.array(json.loads(x)))


	

	# start_time = timeit.default_timer()

	# with Parallel(n_jobs=-1, verbose=5) as parallel:
	# 	accumulator = 0.
	# 	n_iter = 0
	# 	while accumulator < 5:
	# 		results = parallel(delayed(main)(accumulator + i ** 2) for i in range(10))
	# 		accumulator += sum(results)  # synchronization barrier
	# 		n_iter += 1
			
	# print('done!!')


	# print(accumulator, n_iter)     
	# print(timeit.default_timer() - start_time, 'seconds') 



	# image = sys.argv[1]

	
	# Parallel(n_jobs=1, backend="threading")(delayed(main)(i ** 8) for i in range(5))
	

	# start_time = timeit.default_timer()
	# Parallel(n_jobs=-1, backend="threading")(delayed(main)(i ** 8) for i in range(100000))
	# print(timeit.default_timer() - start_time)






