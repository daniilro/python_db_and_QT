'''

'''
from setuptools import setup, find_packages

setup(name="msg_client",
      version="0.0.0.1",
      description="msg_client",
      author="John Pupkin",
      author_email="master@pupkin.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
