from setuptools import setup

setup(name='highwinds',
      version='0.1',
      description='Command line interface to the Highwinds CDN web services',
      url='https://github.com/Highwinds/highwinds',
      author='Mark Cahill',
      author_email='support@highwinds.com',
      license='MIT',
      packages=['highwinds'],
      install_requires=[
          'requests>=2.0.1',
          'PyYAML>=3.10'
      ],
      test_suite='nose.collector',
      tests_require=['nose', 'responses'],
      zip_safe=False)