#!/usr/bin/env python

import argparse
import sys
from copy import deepcopy

from ruamel.yaml import round_trip_dump, round_trip_load
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import StreamMark
from ruamel.yaml.tokens import CommentToken


##
# MERGE
#


def get_type_error(dest, src, current_path):
    return TypeError('Error trying to merge a {0} in a {1} at ({2})'.format(type(src), type(dest), current_path))


def copy_ca_comment_and_ca_end(dest, src):
    # ruamel.yaml.Comment.ca contains 3 attributes : comment, items and end. We just copy comment and end here
    if src.ca and dest.ca:
        if src.ca.comment is not None:
            if dest.ca.comment is None:
                dest.ca.comment = [None, None]
            if src.ca.comment[0] is not None:
                dest.ca.comment[0] = src.ca.comment[0]
            if src.ca.comment[1] is not None and len(src.ca.comment[1]) > 0:
                dest.ca.comment[1] = src.ca.comment[1]
        if len(src.ca.end) > 0:
            dest.ca.end = src.ca.end


def merge(dest, src, current_path=""):
    """
    (Recursively) merge a source object to an dest object (CommentedMap, CommentedSeq, scalar or None)
    and append the current position to current_path
    :return: the merged object
    """
    if isinstance(src, CommentedMap):
        if isinstance(dest, CommentedMap):
            for k in src:
                dest[k] = merge(dest[k], src[k], current_path + '->' + str(k)) if k in dest else src[k]
                if k in src.ca.items and src.ca.items[k][2] and src.ca.items[k][2].value.strip():
                    # copy non empty 'items' comments
                    dest.ca.items[k] = src.ca.items[k]
            copy_ca_comment_and_ca_end(dest, src)
        elif dest is None:
            return src
        else:  # scalar or CommentedSeq
            raise get_type_error(dest, src, current_path)
    elif isinstance(src, CommentedSeq):
        if isinstance(dest, CommentedSeq):
            for i in src:
                dest.append(i)
            copy_ca_comment_and_ca_end(dest, src)
        elif isinstance(dest, CommentedMap):
            raise get_type_error(dest, src, current_path)
        elif dest is None:
            return src
        else:  # scalar
            src.append(dest)
            return src
    elif src is None:
        return dest
    else:  # scalar
        if isinstance(dest, CommentedSeq):
            dest.append(src)
        elif isinstance(dest, CommentedMap):
            raise get_type_error(dest, src, current_path)
        else:  # scalar
            dest = src
    return dest


def successive_merge(contents):
    """
    Successively merge a list of yaml contents by calling merge()
    :param contents: list of yaml contents in str format
    :return: merged yaml in str format
    """
    data = []
    for i in contents:
        data.append(round_trip_load(i, preserve_quotes=True))
    for i in range(-1, -len(contents), -1):
        final_data = merge(data[i - 1], data[i], 'ROOT')
    return final_data


##
# DELETE and COMMENT
##


def str_or_int_map(s):
    return int(s) if is_int(s) else s


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def delete_yaml_item(data, path_to_key, data_contains_list=True):
    """
    Delete a yaml item given its path_to_key (e.g. [foo 0 bar]), and its direct previous comment(s)
    """
    if data_contains_list:
        path_to_key = list(map(str_or_int_map, path_to_key))

    parent = data.mlget(path_to_key[:-1], list_ok=data_contains_list) if len(path_to_key) > 1 else data
    item_key = path_to_key[-1]

    if isinstance(parent, CommentedMap):
        if item_key not in parent:
            raise KeyError("the key \'{}\' does not exist".format(item_key))
        preceding_comments = parent.ca.items.get(item_key, [None, None, None, None])[1]
        del parent[item_key]
    elif isinstance(parent, CommentedSeq):
        if not is_int(item_key) or item_key >= len(parent):
            raise RuntimeError("the key \'{}\' is not an integer or exceeds its parent's length".format(item_key))
        else:
            preceding_comments = deepcopy(parent.ca.items.get(item_key, [None, None, None, None])[1])
            parent.pop(item_key)  # CommentedSet.pop(idx) automatically shifts all ca.items' indexes !
    else:
        raise RuntimeError("Couldn't reach the last item following the path_to_key " + str(path_to_key))

    return data, preceding_comments


def comment_yaml_item(data, path_to_key, data_contains_list=True):
    """
    (EXPERIMENTAL) Comment a yaml item given its path_to_key (e.g. [foo 0 bar]), with comment preservation
    Inspired from https://stackoverflow.com/a/43927974 @cherrot
    """
    if data_contains_list:
        path_to_key = list(map(str_or_int_map, path_to_key))

    parent = data.mlget(path_to_key[:-1], list_ok=data_contains_list) if len(path_to_key) > 1 else data
    item_key = path_to_key[-1]
    deleted_item = item_key

    next_key = None

    if isinstance(parent, CommentedMap):
        if item_key not in parent:
            raise KeyError("the key \'{}\' does not exist".format(item_key))
        # don't just pop the value for item_key that way you lose comments
        # in the original YAML, instead deepcopy and delete what is not needed
        block_copy = deepcopy(parent)
        found = False
        keys = [k for k in parent.keys()]
        for key in reversed(keys):
            if key == item_key:
                found = True
            else:
                if not found:
                    next_key = key
                del block_copy[key]

        # now delete the key and its value, but preserve its preceding comments
        preceding_comments = parent.ca.items.get(item_key, [None, None, None, None])[1]

        if next_key is None:
            if parent.ca.comment is None:
                parent.ca.comment = [None, []]
            if parent.ca.comment[1] is None:
                parent.ca.comment[1] = []
            comment_list = parent.ca.comment[1]
        else:
            comment_list = parent.ca.items.get(next_key, [None, None, None, None])[1]
            if comment_list is None:
                parent.ca.items[next_key] = [None, [], None, None]
                comment_list = parent.ca.items.get(next_key)[1]
        if preceding_comments is not None:
            for c in reversed(preceding_comments):
                comment_list.insert(0, c)
        del parent[item_key]
    elif isinstance(parent, CommentedSeq):
        if not is_int(item_key) or item_key >= len(parent):
            raise RuntimeError("the key \'{}\' is not an integer or exceeds its parent's length".format(item_key))
        else:
            block_copy = deepcopy(parent)
            for i in reversed(range(len(parent))):
                if i != item_key:
                    del block_copy[i]

            next_key = item_key
            preceding_comments = deepcopy(parent.ca.items.get(item_key, [None, None, None, None])[1])
            parent.pop(item_key)  # CommentedSet.pop(idx) automatically shifts all ca.items' indexes !

            if len(parent) == 1 or next_key == len(parent):
                comment_list = parent.ca.end # TODO: fix this, the appended comments don't show up in some case
            else:
                comment_list = parent.ca.items.get(next_key, [None, None, None, None])[1]
                if comment_list is None:
                    parent.ca.items[next_key] = [None, [], None, None]
                    comment_list = parent.ca.items.get(next_key)[1]

            if preceding_comments is not None:
                for c in reversed(preceding_comments):
                    comment_list.insert(0, c)
    else:
        raise RuntimeError("Couldn't reach the last item following the path_to_key " + str(path_to_key))

    key_dept = len(path_to_key) - 1
    if is_int(path_to_key[-1]) and key_dept > 0:
        key_dept = key_dept - 1
    comment_list_copy = deepcopy(comment_list)
    del comment_list[:]

    start_mark = StreamMark(None, None, None, 2 * key_dept)
    skip = True
    for line in round_trip_dump(block_copy).splitlines(True):
        if skip:
            if line.strip(' ').startswith('#'):  # and deleted_item not in line:
                continue
            skip = False
        comment_list.append(CommentToken('#' + line, start_mark, None))
    comment_list.extend(comment_list_copy)

    return data


###
# main and commands
###


def main():
    parser = argparse.ArgumentParser(
        description='A set of CLI tools to manipulate YAML files (merge, delete, comment, etc...) \
         with comment preservation',
        usage='''yaml-tools <command> [<args>]
At the moment there are three commands available:
   merge     Merge two or more yaml files and preserve the comments
   delete    Delete an item (and all its child items) given its path from the input yaml file
   comment   Comment an item (and all its child items) given its path from the input yaml file''')
    parser.add_argument('command', help='Sub-command to run')
    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])
    if args.command == 'merge':
        merge_command()
    elif args.command == 'delete':
        delete_command()
    elif args.command == 'comment':
        comment_command()
    else:
        print('Unrecognized command')
        parser.print_help()
        exit(1)


def merge_command():
    """
    Sub-command, see main()
    """
    parser = argparse.ArgumentParser(
        description='Merge two or more yaml files and preserve the comments')
    parser.add_argument('-i', '--inputs', nargs='+', type=str,
                        help='<Required> List of input yaml files, merged from the last to the first',
                        required=True)
    parser.add_argument('-o', '--output', type=str,
                        help='Path to the output file, or stdout by default')
    parser.add_argument('--indent', type=int,
                        help='Number of space(s) for each indent', default=2)

    args = parser.parse_args(sys.argv[2:])

    file_contents = []
    for f in args.inputs:
        file = open(f, 'r')
        file_contents.append(file.read())
        file.close()

    out_content = successive_merge(file_contents)
    output_file = open(args.output, 'w') if args.output else sys.stdout
    round_trip_dump(out_content, output_file)
    output_file.close()


def delete_command():
    """
    Sub-command, see main()
    """
    parser = argparse.ArgumentParser(
        description='Delete one item from the input yaml file')
    parser.add_argument('path_to_key', type=str, nargs='+',
                        help='<Required> Yaml item to be deleted, e.g. "foo 0 bar"')
    parser.add_argument('-i', '--input', type=str,
                        help='<Required> Path to the input yaml files', required=True)
    parser.add_argument('-o', '--output', type=str,
                        help='Path to the output file, or stdout by default')
    parser.add_argument('--indent', type=int,
                        help='Number of space(s) for each indent', default=2)

    args = parser.parse_args(sys.argv[2:])
    input_file = open(args.input, 'r')
    data = round_trip_load(input_file.read(), preserve_quotes=True)
    input_file.close()

    output_data, _ = delete_yaml_item(data, args.path_to_key, True)

    output_file = open(args.output, 'w') if args.output else sys.stdout
    round_trip_dump(output_data, output_file)
    output_file.close()


def comment_command():  # pragma: no cover
    """
    Sub-command, see main()
    """
    # TODO: refactor this command with delete ?
    parser = argparse.ArgumentParser(
        description='Comment one item from the input yaml file')
    parser.add_argument('path_to_key', type=str, nargs='+',
                        help='<Required> Yaml item to be commented, e.g. "foo 0 bar"')
    parser.add_argument('-i', '--input', type=str,
                        help='<Required> Path to the input yaml file', required=True)
    parser.add_argument('-o', '--output', type=str,
                        help='Path to the output file, or stdout by default')
    parser.add_argument('--indent', type=int,
                        help='Number of space(s) for each indent', default=2)

    args = parser.parse_args(sys.argv[2:])
    input_file = open(args.input, 'r')
    data = round_trip_load(input_file.read(), preserve_quotes=True)
    input_file.close()

    output_data = comment_yaml_item(data, args.path_to_key, True)

    output_file = open(args.output, 'w') if args.output else sys.stdout
    round_trip_dump(output_data, output_file)
    output_file.close()


if __name__ == '__main__':  # pragma: no cover
    main()
