import setuptools

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name='minerva-cli',
    version='0.0.3',
    author="Juha Ruokonen",
    description='Minerva Command Line Interface',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/labsyspharm/minerva-cli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "boto3>=1.14.44",
        "requests",
        "tabulate",
        "minerva-lib==0.0.5",
        "tqdm"
    ],
    dependency_links=[
        'git+https://github.com/labsyspharm/minerva-lib-python@master#egg=minerva-lib'
    ],
    entry_points={
        "console_scripts": [
            "minerva=minerva_cli.minerva:main"
        ]
    },
    use_scm_version={"write_to": "minerva_cli/_version.py"},
    setup_requires=["setuptools_scm"]
)

