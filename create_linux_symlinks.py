#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import os.path
import marisa_trie
import itertools
from argparse import ArgumentParser


CAMEL_CASE_MIN_WORD_LEN = 4
STRIP_LEFT_DIGITS_REGEX = re.compile(r"""(\d*)(.*)""")


def load_vocabulary(path):
    with open(path) as fp:
        return marisa_trie.Trie([w.strip().lower() for w in fp])


def to_camel_case(name, vocabulary):
    if not name:
        yield ''
        return
    first_digits, name = STRIP_LEFT_DIGITS_REGEX.match(name).groups()
    if len(name) < CAMEL_CASE_MIN_WORD_LEN:
        yield first_digits + name.title()
        return
    prefixes = vocabulary.prefixes(name)
    for prefix in prefixes:
        tail = name[len(prefix):]
        first_word = prefix.title()
        for other_words in to_camel_case(tail, vocabulary):
            yield first_digits + first_word + other_words


def to_lower_case_filename(filename):
    return filename.lower()


def to_camel_case_filename(filename, vocabulary):
    filename_parts = filename.rsplit('.', 1)
    extension = filename_parts[1] if len(filename_parts) > 1 else None
    name_parts = filename_parts[0].lower().split('_')
    name_variants = [to_camel_case(p, vocabulary) for p in name_parts]
    at_least_one = False
    for t in itertools.product(*name_variants):
        at_least_one = True
        new_name = '_'.join(t)
        if extension is not None:
            yield '.'.join([new_name, extension])
        else:
            yield new_name

    if not at_least_one:
        raise RuntimeError('Error converting ' + filename + ' to CamelCase. You need to add missing words to vocabulary')


def create_symlink(src, dst, dir_path, dir_fd, force):
    dst_path = os.path.join(dir_path, dst)
    if os.path.exists(dst_path):
        if os.path.islink(dst_path) and force:
            os.remove(dst, dir_fd=dir_fd)
        else:
            logging.info('%s already exists', dst)
            return
    logging.info('Symlink %s -> %s', src, dst)
    os.symlink(src, dst, dir_fd=dir_fd)


def main(args):
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    vocabulary = load_vocabulary(args.vocabulary)
    force = not args.not_overwrite
    for path in args.paths:
        for root, dirs, files, root_fd in os.fwalk(path):
            for filename in files:
                try:
                    if os.path.islink(os.path.join(root, filename)):
                        continue
                    create_symlink(filename, to_lower_case_filename(filename), root, root_fd, force)
                    for camelName in to_camel_case_filename(filename, vocabulary):
                        create_symlink(filename, camelName, root, root_fd, force)
                except Exception as err:
                    if not args.skip_errors:
                        raise
                    logging.error('Failed symlink for %s. Error: %s', filename, err)


if __name__ == '__main__':
    parser = ArgumentParser('Hack for linux: create lowercase and camel-notation symlinks for every file')
    parser.add_argument('-p', '--paths', nargs='+', help='Paths to handle', required=True)
    parser.add_argument('-y', '--vocabulary', default='default_symlinks_vocabulary.txt')
    parser.add_argument('-w', '--not-overwrite', action='store_true', help='Do not overwrite symlink if exists')
    parser.add_argument('-e', '--skip-errors', action='store_true', help='Do not fail on error')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')
    args = parser.parse_args()

    main(args)
