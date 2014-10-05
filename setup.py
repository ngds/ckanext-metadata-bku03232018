from setuptools import setup, find_packages

version = '0.0.1a'

setup(
	name='ckanext-metadata',
	version=version,
	description="Better metadata support than what vanilla CKAN provides",
	long_description='''\
	''',
	classifiers=[],
	keywords='',
	author='Arizona Geological Survey',
	author_email='adrian.sonnenschein@azgs.az.gov',
	url='https://github.com/ngds/ckanext-ngds',
	license='MIT',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext'],
    include_package_data=True,
	zip_safe=False,
	install_requires=[],
    entry_points=
	"""
	[ckan.plugins]

    # Metadata plugin
	metadata=ckanext.metadata.plugin:MetadataPlugin
	""",
)
