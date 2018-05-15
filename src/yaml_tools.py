import sys
import argparse
import ruamel.yaml


def get_type_error(dest, src, path):
    return TypeError('Error trying to merge a {0} in a {1} at {2}'.format(type(src), type(dest), path))


def _merge(dest, src, path=""):
    if isinstance(src, ruamel.yaml.comments.CommentedMap):
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            for k in src:
                dest[k] = _merge(dest[k], src[k], path + '.' + str(k)) if k in dest else src[k]
                if k in src.ca._items and src.ca._items[k][2] and \
                        src.ca._items[k][2].value.strip():
                    dest.ca._items[k] = src.ca._items[k]  # copy non-empty comment
        else:
            raise get_type_error(dest, src, path)
    elif isinstance(src, ruamel.yaml.comments.CommentedSeq):
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            raise get_type_error(dest, src, path)
        elif isinstance(dest, ruamel.yaml.comments.CommentedSeq):
            dest.extend(src)
        else:
            src.append(dest)
            dest = src
    else:
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            raise get_type_error(dest, src, path)
        elif isinstance(dest, ruamel.yaml.comments.CommentedSeq):
            dest.append(src)
        else:
            dest = src
    return dest


def successive_merge(contents):
    data = []
    for i in contents:
        data.append(ruamel.yaml.round_trip_load(i))
    for i in range(-1, -len(contents), -1):
        _merge(data[i - 1], data[i], 'ROOT')
    return data[0]


def merge():
    parser = argparse.ArgumentParser(description='Merge two or more yaml files and preserve the comments')
    parser.add_argument('-i', '--inputs', nargs='+', type=str, help='<Required> List of input yaml files.',
                        required=True)
    parser.add_argument('-o', '--output', type=str, help='Path to the output file, or stdout by default.')
    parser.add_argument('--indent', type=int, help='Number of space(s) for each indent.', default=2)

    args = parser.parse_args(sys.argv[2:])

    file_contents = []
    for f in args.inputs:
        file = open(f, 'r')
        file_contents.append(file.read())
        file.close()

    out_content = successive_merge(file_contents)
    output = open(args.output, 'w') if args.output else sys.stdout

    ruamel.yaml.round_trip_dump(out_content, output, indent=args.indent)


def main():
    parser = argparse.ArgumentParser(
        description='A set of CLI tools to manipulate YAML files (merge, delete, etc...) with comment preservation',
        usage='''yaml-tools <command> [<args>]
At the moment there is only one command available:
   merge     Merge two or more yaml files and preserve the comments''')
    parser.add_argument('command', help='Subcommand to run')
    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])
    if args.command == 'merge':
        merge()
    else:
        print('Unrecognized command')
        parser.print_help()
        exit(1)


if __name__ == '__main__':  # pragma: no cover
    main()
