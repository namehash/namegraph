from setuptools import setup, find_packages

setup(
    name='generator',
    packages=find_packages(),
    version='0.0.1',
    install_requires=[
        'hydra-core==1.2.0',
        'nltk==3.6.7',
        'gensim==4.0.0',
        'pytest',
        'wordninja'
    ]
)
