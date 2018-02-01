import os
from setuptools import setup, find_packages

from flag_slurper import __version__

ROOT = os.path.dirname(__file__)


def read(fname):
    return open(os.path.join(ROOT, fname)).read()


tests_require = [
    'pytest',
    # Until it's fixed for pytest 3.4.0
    # 'pytest-sugar',
    'tox',
    'vcrpy',
]


setup(
    name='flag_slurper',
    version=__version__,
    description='Tool for getting flags from CDC machines',
    long_description=read('README.md'),
    author='Matt Gerst',
    author_email='mattgerst@gmail.com',
    license='MIT',
    packages=find_packages(),

    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'requests',
        'click',
    ],
    tests_require=tests_require,
    extras_require={
        'remote': [
            'paramiko',
            'pyyaml',
        ],
        'tests': tests_require,
    },

    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],

    entry_points={
        'console_scripts': [
            'flag-slurper=flag_slurper.cli:cli',
        ]
    },
    package_data={
        'flag_bearer': ['default.ini'],
    },
)
