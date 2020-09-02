from setuptools import setup, Extension

# cf https://stackoverflow.com/questions/2584595/building-a-python-module-and-linking-it-against-a-macosx-framework
from os import environ
environ['LDFLAGS'] = '-F/Users/jgoldstone/Library/Frameworks -framework i1Pro -L/Users/jgoldstone/lib -li1ProAdapter'

iPAExtension = Extension('i1ProAdapter', include_dirs=['/Users/jgoldstone/include'], sources=['meter/src/i1ProAdapterModule.c'])

setup(
    name="i1ProAdapter",
    version="0.9",
    description="EIEIO meter adapter for i1Pro spectroradiometers",
    ext_modules=[iPAExtension]
)
