from setuptools import setup, find_packages

# Read the contents of your requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the contents of your README file
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='primisai',
    version='0.1.0',
    author='PrimisAI',
    author_email='info@primis.ai',
    description='Nexus is a powerful and flexible Python package for managing AI agents and coordinating complex tasks using LLMs. It provides a robust framework for creating, managing, and interacting with multiple specialized AI agents under the supervision of a central coordinator.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/PrimisAI/nexus',
    packages=find_packages(exclude=['tests*']),
    install_requires=requirements,
    python_requires='>=3.10',
    include_package_data=True,
)
