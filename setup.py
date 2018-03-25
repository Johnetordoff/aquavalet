from setuptools import setup, find_packages

# Taken from option 3 of https://packaging.python.org/guides/single-sourcing-package-version/
setup(
    name='aquavalet',
    version='0.0.0',
    namespace_packages=['aquavalet', 'aquavalet.auth', 'aquavalet.providers'],
    #description='AquaValet Storage Server',
    #author='Center for Open Science',
    #author_email='contact@cos.io',
    #url='https://github.com/CenterForOpenScience/waterbutler',
    packages=find_packages(exclude=("tests*", )),
    package_dir={'aquavalet': 'aquavalet'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    provides=[
        'aquavalet.providers',
    ],
    entry_points={
        'aquavalet.providers': [
            'artifacts = aquavalet.providers.artifacts:ArtifactsProvider',
            'cloudfiles = aquavalet.providers.cloudfiles:CloudFilesProvider',
            'dropbox = aquavalet.providers.dropbox:DropboxProvider',
            'figshare = aquavalet.providers.figshare:FigshareProvider',
            'filesystem = aquavalet.providers.filesystem:FileSystemProvider',
            'github = aquavalet.providers.github:GitHubProvider',
            'gitlab = aquavalet.providers.gitlab:GitLabProvider',
            'bitbucket = aquavalet.providers.bitbucket:BitbucketProvider',
            'osfstorage = aquavalet.providers.osfstorage:OSFStorageProvider',
            'owncloud = aquavalet.providers.owncloud:OwnCloudProvider',
            's3 = aquavalet.providers.s3:S3Provider',
            'dataverse = aquavalet.providers.dataverse:DataverseProvider',
            'box = aquavalet.providers.box:BoxProvider',
            'googledrive = aquavalet.providers.googledrive:GoogleDriveProvider',
            'onedrive = aquavalet.providers.onedrive:OneDriveProvider',
            'googlecloud = aquavalet.providers.googlecloud:GoogleCloudProvider',
        ],
        'aquavalet.providers.tasks': [
            'osfstorage_parity = aquavalet.providers.osfstorage.tasks.parity',
            'osfstorage_backup = aquavalet.providers.osfstorage.tasks.backup',
        ]
    },
)
