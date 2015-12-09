This is a gobject-introspection extension for [hotdoc](https://github.com/hotdoc/hotdoc)

This extension parses gir files to generate documentation for multiple languages
(C, python and javascript), and add gobject-specific symbols (classes, properties,
signals).

It also provides a custom wizard to help people port their projects from
gkt-doc to hotdoc.

### Install instructions:

This extension relies on lxml to parse the gir files.

It also requires libxslt to be installed for the gtk-doc port
wizard to work.

On Fedora 22 the dependencies can be installed with:

```
dnf install libxml2-devel libxslt-devel
```

On Debian / Ubuntu:

```
apt-get install libxml2-dev libxslt1-dev
```

If you use this extension in another environment, please let me know
how you installed these requirements :)

You can then install this extension either through pip:

```
pip install hotdoc_gi_extension
```

Or with setup.py if you checked out the code from git:

```
python setup.py install
```

This will of course work in a virtualenv as well.

### Usage:

Just run hotdoc's wizard for more information once the extension is installed with:

```
hotdoc conf --quickstart
```

> This extension requires the C extension to have been configured in order to be useful.

### Hacking

Checkout the code from github, then run:

```
python setup.py develop
```
