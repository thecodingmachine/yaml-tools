#!/usr/bin/env python3

import argparse
import sys
from copy import deepcopy

from ruamel.yaml import round_trip_dump, round_trip_load
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import StreamMark
from ruamel.yaml.scalarstring import ScalarString
from ruamel.yaml.tokens import CommentToken


##
# utils
##

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


def str_or_int_map(s):
    return int(s) if is_int(s) else s


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


##
# MERGE
#

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
                comment_list = parent.ca.end  # TODO: fix this, the appended comments don't show up in some case
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


##
# NORMALIZE-DOCKER-COMPOSE
##

def is_str_dict(s):
    return isinstance(s, (str, ScalarString)) and ('=' in s or ':' in s)


def only_contains_str_dict(data):
    if isinstance(data, CommentedMap):
        for k in data:
            if not is_str_dict(data[k]):
                return False
    elif isinstance(data, CommentedSeq):
        for v in data:
            if not is_str_dict(v):
                return False
    else:
        return False

    return True


def convert_str_to_key_value(string, separators=(':', '=')):
    """
    :param string: in 'foo:bar' or 'foo=bar' format
    :param separators:
    :return: (key, value)|(None, None)
    """
    sep = ''
    for s in separators:
        if s in string:
            sep = s
    if sep != '':
        array = [a.strip(' ') for a in string.split(sep)]
        return array[0], array[1]
    return None, None


def convert_commented_seq_to_dict(seq):
    """
    :param seq: CommentedSeq
    :return: CommentedMap|CommentedSeq
    """
    if len(seq) > 0 and only_contains_str_dict(seq):
        seq_copy = deepcopy(seq)
        data = CommentedMap()
        copy_ca_comment_and_ca_end(data, seq_copy)
        for i in range(len(seq_copy)):
            k, v = convert_str_to_key_value(seq_copy[i])
            data[k] = v
            data.ca.items[k] = seq_copy.ca.items.get(i, [None, None, None, None])
        return data
    return seq


def delete_duplicated_items(service, key):
    """
    Given a (docker-compose) service, delete all duplicated items (and its preceding comments)
    from an array given by the key (e.g. volumes or env_file)
    :param service: docker-compose yaml service
    :param key: key to an array
    :return: service
    """
    if key in service and isinstance(service[key], CommentedSeq):
        array = service[key]
        del_indexes = set()
        i1 = -1
        for item1 in array:
            i1 = i1 + 1
            i2 = -1
            for item2 in array:
                i2 = i2 + 1
                if i1 != i2 and i1 not in del_indexes and str(item1) == str(item2):
                    del_indexes.add(i2)
        for i in reversed(list(del_indexes)):
            array.pop(i)
    return service


def normalize_docker_compose(content):
    """
    If content is a CommentedMap, convert all key-value string (e.g. 'foo=bar' or '80:8080')
    to key-value dicts inside the services' `labels` and `environment` fields,
    also delete all duplicated volumes and env_file (and its preceding comments) for each services
    """
    data = round_trip_load(content, preserve_quotes=True)
    if isinstance(data, CommentedMap):
        keys = [key.lower() for key in data.keys()]
        if 'services' in keys:
            services = data['services']
            for k in services:
                if 'labels' in services[k] and isinstance(services[k]['labels'], CommentedSeq):
                    services[k]['labels'] = convert_commented_seq_to_dict(services[k]['labels'])
                if 'environment' in services[k] and isinstance(services[k]['environment'], CommentedSeq):
                    services[k]['environment'] = convert_commented_seq_to_dict(services[k]['environment'])
                delete_duplicated_items(services[k], 'volumes')
                delete_duplicated_items(services[k], 'env_file')
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
    elif args.command == 'normalize-docker-compose':
        normalize_docker_compose_command()
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

    args = parser.parse_args(sys.argv[2:])
    input_file = open(args.input, 'r')
    data = round_trip_load(input_file.read(), preserve_quotes=True)
    input_file.close()

    output_data = comment_yaml_item(data, args.path_to_key, True)

    output_file = open(args.output, 'w') if args.output else sys.stdout
    round_trip_dump(output_data, output_file)
    output_file.close()


def normalize_docker_compose_command():
    """
    Sub-command, see main()
    """
    parser = argparse.ArgumentParser(
        description='Normalize the input docker-compose file, then write it in the output')
    parser.add_argument('-i', '--input', type=str,
                        help='<Required> Path to the input yaml file', required=True)
    parser.add_argument('-o', '--output', type=str,
                        help='Path to the output file, or stdout by default')

    args = parser.parse_args(sys.argv[2:])
    input_file = open(args.input, 'r')
    content = input_file.read()
    input_file.close()

    output_data = normalize_docker_compose(content)

    output_file = open(args.output, 'w') if args.output else sys.stdout
    round_trip_dump(output_data, output_file)
    output_file.close()


if __name__ == '__main__':  # pragma: no cover
    main()
