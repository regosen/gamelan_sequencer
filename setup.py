# to test locally:
# python setup.py develop
#
# to deploy:
# rm -rf ./dist
# python setup.py sdist bdist_wheel
# python -m twine upload --repository pypi dist/*
#
# more info here:
# https://packaging.python.org/tutorials/packaging-projects/#uploading-your-project-to-pypi

# NOTE: make sure you have the latest setuptools or the requirements may not get installed correctly.
# python -m pip install --upgrade pip setuptools

import setuptools

setuptools.setup(name = 'gamelan_sequencer',
    version = '1.2.0',
    author = 'Rego Sen',
    author_email = 'regosen@gmail.com',
    url = 'https://github.com/regosen/gamelan_sequencer',
    description = 'Python Sequencer for Gamelan Music',
    long_description = open('README.md', 'r').read(),
    long_description_content_type = 'text/markdown',
    license = 'MIT',
    keywords = 'music songwriting indonesia javanese balinese kepatihan gamelan',
    packages = setuptools.find_packages(),
    package_dir = {'gamelan_sequencer': 'gamelan_sequencer'},
    package_data = {'gamelan_sequencer': ['gamelan_sequencer/samples/*.json']},
    include_package_data = True,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Editors'
    ],
    install_requires = [
        'scipy',
    ],
    entry_points = {
        'console_scripts': [
            'gamelan_sequencer = gamelan_sequencer.__main__:main',
        ]
    },
)