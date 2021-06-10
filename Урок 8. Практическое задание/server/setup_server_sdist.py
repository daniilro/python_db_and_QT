'''

'''
from setuptools import setup, find_packages
setup(name="msg_server",
      version="0.0.0.1",
      description="msg_server",
      author="anonymous",
      author_email="anonymous@null.null",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
