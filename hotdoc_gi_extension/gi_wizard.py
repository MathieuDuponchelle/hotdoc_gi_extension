# -*- coding: utf-8 -*-
#
# Copyright © 2015,2016 Mathieu Duponchelle <mathieu.duponchelle@opencreed.com>
# Copyright © 2015,2016 Collabora Ltd
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess

from lxml import etree

from hotdoc.core.wizard import HotdocWizard
from hotdoc.parsers.gtk_doc_parser import GtkDocStringFormatter
from hotdoc.utils.patcher import Patcher
from hotdoc.utils.utils import get_all_extension_classes
from hotdoc.utils.wizard import Skip

from .transition_scripts.sgml_to_sections import parse_sections, convert_to_markdown

PROMPT_GI_INDEX=\
"""
You will now need to provide a markdown index for introspected
symbols.

You can learn more about standalone markdown files at [FIXME],
for now suffice to say that these files provide the basic skeleton
for the output documentation, and list which symbols should be
documented in which page.

The index is the root, it will usually link to various subpages.

There are three ways to provide this index:

- Converting existing gtk-doc files.
- Generating one

You can of course skip this phase for now, and come back to it later.

"""

PROMPT_GTK_PORT_MAIN=\
"""
Porting from gtk-doc is a bit involved, and you will
want to manually go over generated markdown files to
improve pandoc's conversion (or contribute patches
to pandoc's docbook reader if you know haskell. I don't).

You'll want to make sure you have built the documentation
with gtk-doc first, it should be easy as checking that
there is an xml directory in the old documentation folder.

If not, you'll want to verify you have run make,
and possibly run ./configure --enable-gtk-doc in the
root directory beforehand.

Press Enter once you made sure you're all set. """

PROMPT_SECTIONS_FILE=\
"""
Good.

The first thing this conversion tool will need is the
path to the "sections" file. It usually is located in
the project's documentation folder, with a name such as
'$(project_name)-sections.txt'.

Path to the sections file ? """

PROMPT_SECTIONS_CONVERSION=\
"""
Thanks, I don't know what I would do without you.

Probably just sit there idling.

Anyway, the next step is to go over certain comments
in the source code and either rename them or place
them in the markdown files.

These comments are the "SECTION" comments, which
either document classes and should stay in the source
code, or were generic comments that have nothing to do
in the source code and belong in the standalone markdown
pages.

FYI, I have found %d section comments and %d class comments.

Don't worry, I can do that for you, I'll just need
your permission to slightly modify the source files.

Permission granted [y,n]? """

PROMPT_COMMIT=\
"""
Sweet.

Should I commit the files I modified [y,n]? """

PROMPT_DESTINATION=\
"""
Nice.

We can now finalize the port, by generating the standalone
markdown pages that will form the skeleton of your documentation.

I'll need you to provide me with a directory in which
to output these files (markdown_files seems like a pretty sane
choice but feel free to go wild).

If the directory does not exist it will be created.

Where should I write the markdown pages ? """

PROMPT_SGML_FILE=\
"""
I'll also need the path to the sgml file, it should look
something like $(project_name)-docs.sgml

Path to the SGML file ? """


def get_section_comments(wizard):
    gir_file = wizard.config.get('gir_file')
    if not os.path.exists(gir_file):
        gir_file = wizard.resolve_config_path(gir_file)

    root = etree.parse(gir_file).getroot()
    xns = root.find("{http://www.gtk.org/introspection/core/1.0}namespace")
    ns = xns.attrib['name']
    xclasses = root.findall('.//{http://www.gtk.org/introspection/core/1.0}class')

    class_names = set({})

    for xclass in xclasses:
        class_names.add(ns + xclass.attrib['name'])

    sections = parse_sections('hotdoc-tmp-sections.txt')
    translator = GtkDocStringFormatter()

    section_comments = {}
    class_comments = []

    for comment in wizard.comments.values():
        if not comment.name.startswith('SECTION:'):
            continue
        structure_name = comment.name.split('SECTION:')[1]
        section = sections.get(structure_name)
        if section is None:
            print "That's weird"
            continue

        section_title = section.find('TITLE')
        if section_title is not None:
            section_title = section_title.text
            if section_title in class_names:
                new_name = ('%s::%s:' % (section_title,
                    section_title))
                class_comments.append(comment)
                comment.raw_comment = comment.raw_comment.replace(comment.name,
                        new_name)
                continue

        comment.raw_comment = ''
        comment.description = translator.translate(comment.description,
                'markdown')
        if comment.short_description:
            comment.short_description = \
            translator.translate(comment.short_description, 'markdown')
        section_comments[structure_name] = comment

    return section_comments, class_comments

def patch_comments(wizard, patcher, comments):
    if not comments:
        return

    for comment in comments:
        patcher.patch(comment.filename, comment.lineno - 1,
                comment.endlineno, comment.raw_comment)
        if comment.raw_comment == '':
            for other_comment in comments:
                if (other_comment.filename == comment.filename and
                        other_comment.lineno > comment.endlineno):
                    removed = comment.endlineno - comment.lineno
                    other_comment.lineno -= removed
                    other_comment.endlineno -= removed

    if wizard.git_interface is None:
        return

    if wizard.git_interface.repo_path is not None:
        wizard.before_prompt()
        if wizard.ask_confirmation(PROMPT_COMMIT):

            for comment in comments:
                wizard.git_interface.add(comment.filename)

            commit_message = "Port to hotdoc: convert class comments"
            wizard.git_interface.commit('hotdoc', 'hotdoc@hotdoc.net', commit_message)

def translate_section_file(sections_path):
    module_path = os.path.dirname(__file__)
    trans_shscript_path = os.path.join(module_path, 'transition_scripts',
            'translate_sections.sh')
    cmd = [trans_shscript_path, sections_path, 'hotdoc-tmp-sections.txt']
    subprocess.check_call(cmd)
def port_from_gtk_doc(wizard):
    # We could not get there if c extension did not exist
    CExtClass = get_all_extension_classes(sort=False)['c-extension']
    CExtClass.validate_c_extension(wizard)
    patcher = Patcher()

    wizard.wait_for_continue(PROMPT_GTK_PORT_MAIN)
    wizard.prompt_executable('pandoc')
    sections_path = wizard.prompt_key('sections_file',
            prompt=PROMPT_SECTIONS_FILE, store=False,
            validate_function=wizard.check_path_is_file)
    translate_section_file(sections_path)

    section_comments, class_comments = get_section_comments(wizard)

    wizard.before_prompt()

    if not wizard.ask_confirmation(PROMPT_SECTIONS_CONVERSION %
            (len(section_comments), len(class_comments))):
        raise Skip

    patch_comments(wizard, patcher, class_comments +
            section_comments.values())
    sgml_path = wizard.prompt_key('sgml_path',
            prompt=PROMPT_SGML_FILE, store=False,
            validate_function=wizard.check_path_is_file)
    folder = wizard.prompt_key('markdown_folder',
            prompt=PROMPT_DESTINATION, store=False,
            validate_function=wizard.validate_folder)

    convert_to_markdown(sgml_path, 'hotdoc-tmp-sections.txt', folder,
            section_comments, 'gobject-api.markdown')

    os.unlink('hotdoc-tmp-sections.txt')

    return 'gobject-api.markdown'

class GIWizard(HotdocWizard):
    def do_quick_start(self):
        if not HotdocWizard.group_prompt(self):
            return False

        res = HotdocWizard.do_quick_start(self)

        self.before_prompt()
        try:
            choice = self.propose_choice(
                    ["Create index from a gtk-doc project",
                    ],
                    extra_prompt=PROMPT_GI_INDEX
                    )

            if choice == 0:
                self.config['gi_index'] = port_from_gtk_doc(self)
        except Skip:
            pass

        return res

    def get_index_path(self):
        return 'gobject-api'

    def get_index_name(self):
        return 'GObject API'

    def group_prompt(self):
        return True
