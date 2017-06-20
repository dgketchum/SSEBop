# =============================================================================================
# Copyright 2017 dgketchum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================================


from setuptools import setup

# os.environ['TRAVIS_CI'] = 'True'

tag = '0.0.1'

setup(name='ssebop',
      version=tag,
      description='The Operational Simplified Surface Energy Balance',
      setup_requires=[],
      install_requires=['Click', 'numpy==1.12.1', 'requests', 'netCDF4', 'xlrd', 'future', 'setuptools-yaml', 'xarray',
                        'pandas', 'rasterio'],
      py_modules=['ssebop'],
      license='Apache',
      entry_points='''
        [console_scripts]
        ssebop=app.cli:cli
        ''',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: GIS',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3.5'],
      keywords='SSEB operational evapotranspiration algorithm',
      author='David Ketchum (code), Gabriel Senay (algorithm)',
      author_email='dgketchum at gmail dot com',
      platforms='Posix; MacOS X; Windows',
      packages=[''],
      download_url='https://github.com/{}/{}/archive/{}.tar.gz'.format('dgketchum', 'core', tag),
      url='https://github.com/dgketchum',
      test_suite='tests.test_suite.suite',
      )

# ========================= EOF ====================================================================
