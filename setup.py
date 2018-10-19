from setuptools import setup, find_packages

# Taken from option 3 of https://packaging.python.org/guides/single-sourcing-package-version/
setup(
    name='aquavalet',
    version='0.0.0',
    namespace_packages=['aquavalet', 'aquavalet.providers'],
    description='AquaValet Storage Server',
    packages=find_packages(exclude=("tests*", )),
    package_dir={'aquavalet': 'aquavalet'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    provides=[
        'aquavalet.providers',
    ],
    entry_points={
        'aquavalet.providers': [
            'artifacts = aquavalet.providers.artifacts:ArtifactsProvider',
            'filesystem = aquavalet.providers.filesystem:FileSystemProvider',
            'osfstorage = aquavalet.providers.osfstorage:OSFStorageProvider',
        ]
    },
)
