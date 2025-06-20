import sys
import os

if getattr(sys, 'frozen', False):
    # 打包后
    base_dir = os.path.dirname(sys.executable)
else:
    # 源码运行
    base_dir = os.path.dirname(os.path.abspath(__file__))
