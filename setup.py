from setuptools import setup, find_packages

setup(
    name = "hotdoc_gi_extension",
    version = "0.6.6",
    keywords = "gobject-introspection C hotdoc",
    url='https://github.com/hotdoc/hotdoc_gi_extension',
    author_email = 'mathieu.duponchelle@opencreed.com',
    license = 'LGPL',
    description = "An extension for hotdoc that parses gir files",
    author = "Mathieu Duponchelle",
    packages = find_packages(),

    package_data = {
        '': ['*.html'],
        'hotdoc_gi_extension.transition_scripts': ['translate_sections.sh'],
    },

    entry_points = {'hotdoc.extensions': 'get_extension_classes = hotdoc_gi_extension.gi_extension:get_extension_classes'},
    install_requires = [
        'lxml',
    ],
)
