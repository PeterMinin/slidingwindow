from setuptools import setup

setup(
	name = 'slidingwindow',
	version = '0.0.1',
	description = 'Sliding Window library for image processing in Python',
	url = 'https://github.com/adamrehn/slidingwindow',
	author = 'Adam Rehn',
	author_email = 'adam@adamrehn.com',
	license = 'MIT',
	packages = ['slidingwindow'],
	zip_safe = False,
	install_requires = [
		'numpy'
	]
)