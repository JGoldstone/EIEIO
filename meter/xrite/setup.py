from setuptools import setup, Extension

# cf https://stackoverflow.com/questions/2584595/building-a-python-module-and-linking-it-against-a-macosx-framework
from os import environ
environ['LDFLAGS'] = '-F/Library/Frameworks -framework i1Pro3 -framework i1Pro -L/usr/local/lib -li1ProAdapter'

iPAExtension = Extension('i1ProAdapter',
                         include_dirs=['/usr/local/include'],
                         sources=['i1ProAdapterModule.c'])

# When this script is invoked, the invocation needs to have a single argument 'install' passed on
# the invocation. For PyCharm, this means setting the value of the relevant configuration's
# 'Parameters' field to 'install'.
setup(
    name="i1ProAdapter",
    version="0.9",
    description="EIEIO meter adapter for i1Pro spectroradiometers",
    ext_modules=[iPAExtension]
)
