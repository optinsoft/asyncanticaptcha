from distutils.core import setup
import re

s = open('asyncanticaptcha/version.py').read()
v = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", s, re.M).group(1)

setup(name='asyncanticaptcha',
    version=v,
    description='Async API wrapper for anti-captcha',
    install_requires=["aiohttp","certifi"],
    author='optinsoft',
    author_email='optinsoft@gmail.com',
    keywords=['anti-captcha','async'],
    url='https://github.com/optinsoft/asyncanticaptcha',
    packages=['asyncanticaptcha']
)