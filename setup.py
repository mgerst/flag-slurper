import os
from setuptools import setup, find_packages
from flag_slurper import __version__

ROOT = os.path.dirname(__file__)


def read(fname):
    return open(os.path.join(ROOT, fname)).read()


install_requires = [
    'requests>=2.20.0',
    'click==6.7',
    'pyyaml>=4.2b1',
    'schema==0.6.7',
    'jinja2==2.10.1',
    'peewee==3.9.5',
    'terminaltables==3.1.0',
    'dnspython==1.15.0',
    'Faker==1.0.7',
]


tests_require = [
    'pytest==3.4.2',
    'pytest-cov==2.5.1',
    'pytest-sugar==0.9.1',
    'pytest-mock==1.7.1',
    'tox==2.9.1',
    'vcrpy==1.11.1',
    'responses==0.8.1',
    'pretend==1.0.8',
    'hypothesis==3.57.0',
]


docs_require = [
    'sphinx',
    'sphinx-autobuild',
    'sphinx_rtd_theme',
]

dev_requires = [
    'bumpversion==0.5.3',
    'twine==1.10.0',
]


setup(
    name='flag_slurper',
    version='0.9.0',
    description='Tool for getting flags from CDC machines',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Matt Gerst',
    author_email='mattgerst@gmail.com',
    license='MIT',
    packages=find_packages(),

    setup_requires=[
        'pytest-runner',
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'remote': [
            'paramiko==2.6.0',
        ],
        'parallel': [
            'psycopg2-binary==2.7.4',  # You need -binary to get the wheels
        ],
        'tests': tests_require,
        'docs': docs_require,
        'dev': dev_requires,
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
