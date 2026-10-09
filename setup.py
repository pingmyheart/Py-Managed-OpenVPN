import warnings

from setuptools import setup, find_packages

# Suppress all warnings
warnings.filterwarnings("ignore")

setup(
    name='py-managed-openvpn',
    version='0.0.1.dev0',
    packages=find_packages()
)
