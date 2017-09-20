from setuptools import setup


setup(
    name='luap',
    author='TitanSnow',
    author_email='tttnns1024@gmail.com',
    version='1.0.dev1',
    url='https://github.com/TitanSnow/luap',
    description='A lua REPL written in python',
    long_description=open('README.rst').read(),
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Other Scripting Engines',
        'Topic :: Software Development :: Interpreters',
    ],
    packages=('luap',),
    install_requires=(
        'prompt_toolkit>=1.0.4, <2',
        'ffilupa>=2.0.0.dev1, <3',
        'pygments',
    ),
    entry_points={
        'console_scripts': (
            'luap = luap:embed',
        ),
    },
)
