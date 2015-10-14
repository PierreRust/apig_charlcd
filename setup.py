from setuptools import setup, find_packages


with open('README.md', 'r') as f:
    README = f.read()


setup(name='apig_charlcd',
      version='0.0.1',
      description='asyncio-based library to drive character LCD screens ',
      long_description=README,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers"

          "License :: OSI Approved :: Apache Software License",

          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3.4",

          "Topic :: System :: Hardware :: Hardware Drivers",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      author='Pierre Rust',
      author_email='pierre.rust@gmail.com',
      url='https://github.com/PierreRust/apig_charlcd',

      keywords=['lcd', 'pigpio', 'asyncio', 'raspberry'],
      install_requires=[
          'apigpio',
      ],
      packages=find_packages()
      )
