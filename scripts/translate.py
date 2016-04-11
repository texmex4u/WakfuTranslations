#!/usr/bin/env python

# Copyright (c) 2016 Texmex <texmex@wakfu-german.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, collections, datetime, hashlib, re
import polib

from pytz import timezone
from datetime import datetime

languages = {
    'de': 'German'
}

filters = {
    'user-interface': lambda key: not key.startswith('content.'),
    'attacks': lambda key: key.startswith('content.3.'),
    'attack-descriptions': lambda key: key.startswith('content.4.') or key.startswith('content.5.'),
    'combat-objects': lambda key: key.startswith('content.6.'),
    'mobs': lambda key: key.startswith('content.7.'),
    'states': lambda key: key.startswith('content.8.'),
    'state-descriptions': lambda key: key.startswith('content.9.'),
    'effects': lambda key: key.startswith('content.10.'),
    'world-entities': lambda key: key.startswith('content.12.'),
    'effect-descriptions': lambda key: key.startswith('content.13.') or key.startswith('content.33.'),
    'item-types': lambda key: key.startswith('content.14.') or key.startswith('content.37.'),
    'items': lambda key: key.startswith('content.15.'),
    'item-descriptions': lambda key: key.startswith('content.16.'),
    'sets': lambda key: key.startswith('content.20.'),
    'professions': lambda key: key.startswith('content.22.') or key.startswith('content.43.'),
    'book-covers': lambda key: key.startswith('content.24.'),
    'task-logs': lambda key: key.startswith('content.25.'),
    'env-quests': lambda key: key.startswith('content.26.'),
    'env-quest-tasks': lambda key: key.startswith('content.28.'),
    'effect-logs': lambda key: key.startswith('content.30.'),
    'titles': lambda key: key.startswith('content.34.'),
    'signs': lambda key: key.startswith('content.35.'),
    'interactive-entities': lambda key: key.startswith('content.36.') or key.startswith('content.59.') or key.startswith('content.79.') or key.startswith('content.82.'),
    'mob-types': lambda key: key.startswith('content.38.'),
    'nations': lambda key: key.startswith('content.39.'),
    'government-descriptions': lambda key: key.startswith('content.40.'),
    'recipes': lambda key: key.startswith('content.46.'),
    'mob-chatter': lambda key: key.startswith('content.47.'),
    'clan-members': lambda key: key.startswith('content.48.'),
    'clan-member-chatter': lambda key: key.startswith('content.49.'),
    'clan-member-effects': lambda key: key.startswith('content.50.') or key.startswith('content.51.'),
    'weather-options': lambda key: key.startswith('content.52.'),
    'weather-descriptions': lambda key: key.startswith('content.53.'),
    'places': lambda key: key.startswith('content.54.'),
    'government-ranks': lambda key: key.startswith('content.57.'),
    'emote-logs': lambda key: key.startswith('content.60.'),
    'special-places': lambda key: key.startswith('content.61.') or key.startswith('content.66.'),
    'achievements': lambda key: key.startswith('content.62.'),
    'achievement-descriptions': lambda key: key.startswith('content.63.'),
    'achievement-tasks': lambda key: key.startswith('content.64.'),
    'achievement-task-descriptions': lambda key: key.startswith('content.65.'),
    'book-texts': lambda key: key.startswith('content.67.'),
    'clan-member-dialogs': lambda key: key.startswith('content.75.'),
    'clan-member-dialog-choices': lambda key: key.startswith('content.76.'),
    'place-banners': lambda key: key.startswith('content.61.') or key.startswith('content.77.') or key.startswith('content.88.'),
    'emotes': lambda key: key.startswith('content.80.'),
    'clan-member-job': lambda key: key.startswith('content.90.'),
    'clan-member-sex': lambda key: key.startswith('content.91.'),
    'clan-member-height': lambda key: key.startswith('content.92.'),
    'clan-member-weight': lambda key: key.startswith('content.93.'),
    'clan-member-profile': lambda key: key.startswith('content.94.'),
    'laws': lambda key: key.startswith('content.97.'),
    'law-descriptions': lambda key: key.startswith('content.98.'),
}

RE_PROPERTY = re.compile(r'([^=]+)=(.*)\n')
def iter_properties(f):
    l = 0
    for line in f:
        l += 1
        m = RE_PROPERTY.match(line.decode('utf8'))
        if m is None:
            raise ValueError("Invalid line #%d: %s" % (l, line))
        else:
            yield m.group(1), m.group(2).replace('\\n', '\n')

def load_properties(f):
    return collections.OrderedDict(iter_properties(f))

def write_property(f, key, value):
    f.write('%s=%s\n' % (key.encode('utf8'), value.replace('\n', '\\n').encode('utf8')))

def quick_hash(s):
    return hashlib.md5(s.encode('utf8')).digest()

class TranslationCategory(object):
    def __init__(self, name, filter, version, rev_date, language):
        self.name = name
        self.filter = filter

        if not os.path.exists(name):
            os.mkdir(name)

        self.po_en = polib.POFile()
        self.po_en.metadata = {
            'Project-Id-Version': '%s-%s' % (name, version),
            'PO-Revision-Date': rev_date,
            'Language-Team': 'English',
            'Language': 'en',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit'
        }

        self.po_target = polib.POFile()
        self.po_target.metadata = {
            'Project-Id-Version': '%s-%s' % (name, version),
            'PO-Revision-Date': rev_date,
            'Language-Team': languages[language],
            'Language': language,
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit'
        }

        # Load existing translations
        self.dict_target = {}
        self.po_target_file = os.path.join(name, '%s.po' % language)
        if os.path.exists(self.po_target_file):
            for entry in polib.pofile(self.po_target_file):
                if entry.msgstr != '':
                    self.dict_target[entry.comment] = entry.msgstr

        self.dups = {}

    def add(self, key, value_fr, value_en, value_target):
        if not self.filter(key):
            return False

        h = quick_hash(value_fr + value_en)
        if not self.dups.has_key(h):
            self.dups[h] = True
            self.po_en.append(polib.POEntry(msgid=value_fr, msgstr=value_en, comment=key))
            self.po_target.append(polib.POEntry(msgid=value_fr, msgstr=self.dict_target.get(key, value_target), comment=key))

        return True

    def get(self, key, value_fr, value_en):
        if not self.filter(key):
            return None

        h = quick_hash(value_fr + value_en)
        value_target = self.dups.get(h)
        if value_target is not None:
            return value_target

        value_target = self.dict_target.get(key, value_en)
        if value_target == '':
            value_target = value_fr

        self.dups[h] = value_target
        return value_target

    def save(self):
        self.po_en.save(os.path.join(self.name, 'en.po'))
        self.po_target.save(self.po_target_file)

def make_categories(version, rev_date, language):
    categories = []
    for name, filter in filters.iteritems():
        categories.append(TranslationCategory(name, filter, version, rev_date, language))
    categories.append(TranslationCategory('uncategorized', lambda key: True, version, rev_date, language))
    return categories

def disassemble_translations(texts_fr, texts_en, texts_target, categories):
    counter = 0
    for key, value_fr in texts_fr.iteritems():
        if value_fr == '':
            continue

        value_fr = value_fr
        value_en = texts_en.get(key, '')
        value_target = texts_target.get(key, '')
        for category in categories:
            if category.add(key, value_fr, value_en, value_target):
                break

        counter += 1
    return counter

def assemble_translations(texts_fr, texts_en, texts_target, categories):
    counter = 0
    for key, value_fr in texts_fr.iteritems():
        if value_fr == '':
            texts_target[key] = ''
            continue

        value_fr = value_fr
        value_en = texts_en.get(key, '')
        for category in categories:
            value_target = category.get(key, value_fr, value_en)
            if value_target is not None:
                texts_target[key] = value_target
                break

        counter += 1
    return counter

if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser()
    parser.add_argument("language", nargs="?", help="Target language", choices=languages.keys(), default="de")
    parser.add_argument("version", nargs="?", help="Game version", default="1")
    parser.add_argument("-a", "--assemble", help="Assemble the target properties file instead of disassembling", action="store_true")

    args = parser.parse_args()

    if not os.path.exists('texts_fr.properties') and not os.path.exists('texts_en.properties'):
        print "Please provide at least 'texts_fr.properties' and 'texts_en.properties' in the current folder."
        sys.exit(1)

    print "Reading 'texts_fr.properties'..."
    with open('texts_fr.properties', 'rb') as f:
        texts_fr = load_properties(f)

    print "Reading 'texts_en.properties'..."
    with open('texts_en.properties', 'rb') as f:
        texts_en = load_properties(f)

    filename = 'texts_%s.properties' % args.language
    if not args.assemble and os.path.exists(filename):
        print "Reading '%s'..." % filename
        with open(filename, 'rb') as f:
            texts_target = load_properties(f)
    else:
        texts_target = collections.OrderedDict()

    print "Preparing..."
    rev_date = datetime.now(timezone('Europe/Berlin')).replace(microsecond=0).isoformat(' ')
    categories = make_categories(args.version, rev_date, args.language)

    print "Processing..."
    if args.assemble:
        entries_count = assemble_translations(texts_fr, texts_en, texts_target, categories)
    else:
        entries_count = disassemble_translations(texts_fr, texts_en, texts_target, categories)

    print "Saving..."
    if args.assemble:
        with open(filename, 'wb') as f:
            for key, value in texts_target.iteritems():
                write_property(f, key, value)
    else:
        for category in categories:
            category.save()

    print "All done. %d entries processed." % entries_count
