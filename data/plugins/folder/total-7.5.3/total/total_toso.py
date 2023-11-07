# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表编译so
# +-------------------------------------------------------------------

import os
import shutil
from distutils.core import setup
from Cython.Build import cythonize

modules = [
	os.path.abspath("./total_main.py")
]

to_path = os.path.abspath(".")

key = '.cpython-37m-x86_64-linux-gnu'
for module in modules:
	print(module)
	setup(ext_modules=cythonize(module, compiler_directives={"language_level": "3"}), script_args=["build_ext", "-b", to_path])
	# output_so = os.path.join(to_path, os.path.splitext(os.path.split(module)[1])[0]) + key + ".so"
	output_c = os.path.join(to_path, os.path.splitext(os.path.split(module)[1])[0]) + ".c"
	new_so = os.path.join(to_path, os.path.splitext(os.path.split(module)[1])[0]) + ".so"

	# if os.path.exists(output_so):
	# 	os.rename(output_so, new_so)
	if os.path.exists(output_c):
		os.remove(output_c)

if os.path.exists('./build'):
    shutil.rmtree('./build')