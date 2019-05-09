#!/usr/bin/env python3

import os
import platform

py_impl = platform.python_implementation()

if (
    os.environ.get('ANYBLOK_DATABASE_DRIVER', 'postgresql') == 'postgresql' and
    py_impl == 'PyPy'
):
    driver = 'postgresql+psycopg2cffi'
    os.environ.update(ANYBLOK_DATABASE_DRIVER=driver)
