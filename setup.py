from setuptools import setup, find_packages
from PDB2MC.version import version

setup(
    name='PDB2MC',
    version=version,
    packages=find_packages(),
    url='https://github.com/markus-nevil/mcpdb',
    author='Markus Nevil',
    author_email='nevil@email.unc.edu',
    description='A program that converts PDB files to Minecraft functions',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'PyQt6',
        'pandas',
        'numpy',
        'markdown',
        'opencv-python',
        'scipy',
        'tifffile'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Education',
        'Topic :: Games/Entertainment',
        'Operating System :: Microsoft :: Windows :: Windows 10'
    ],
    python_requires='>=3.11',
    entry_points={
        'console_scripts': [
            'PDB2MC = PDB2MC.run_PDB2MC:main',
        ],
    },
    package_data={
        'PDB2MC': ['README.md', 'chains.txt', 'pack.mcmeta'],
        'UI': ['images/*', 'presets/*', 'images/icons/*'],
    },
)

#############
# For compiling
# pyinstaller --onefile --windowed --name=PDB2MC --icon=UI/images/icons/logo.png --add-data "UI;UI" --add-data "PDB2MC/chains.txt;PDB2MC" --add-data "P
# DB2MC/pack.mcmeta;PDB2MC" --add-data "README.md;." PDB2MC/run_PDB2MC.py
#
#############