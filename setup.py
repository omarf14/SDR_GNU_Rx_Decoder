#!/usr/bin/env python

from distutils.core import setup, Extension


fec_module = Extension(
    'fec',
    sources=[
        'fec/rs.c',
        'fec/viterbi.c',
        'fec/randomizer.c',
      #   'fec/rs.h',
      #   'fec/viterbi.h',
      #   'fec/randomizer.h'
    ],
    include_dirs=['fec']
)


setup(name='bbctl',
      version='1.0',
      description='BlueBox control program',
      author='Jeppe Ledet-Pedersen',
      author_email='jlp@satlab.org',
      url='http://www.github.org/satlab/bluebox/',
      scripts=['bbctl'],
      py_modules=['bluebox', 'fec'],
      ext_modules=[fec_module])
