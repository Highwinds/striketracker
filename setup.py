from setuptools import setup

setup(name='striketracker',
      version='0.1',
      description='Command line interface to the Highwinds CDN',
      url='https://github.com/Highwinds/striketracker',
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