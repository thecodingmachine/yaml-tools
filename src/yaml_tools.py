import sys
import argparse
import ruamel.yaml


def get_type_error(dest, src, path):
    return TypeError("Error trying to merge a {0} in a {1} at {2}".format(type(src), type(dest), path))


def update(dest, src, path=""):
    if isinstance(src, ruamel.yaml.comments.CommentedMap):
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            for k in src:
                dest[k] = update(dest[k], src[k], path + "." + str(k)) if k in dest else src[k]
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


def merge_yaml(contents):
    data = []
    for i in contents:
        data.append(ruamel.yaml.round_trip_load(i))
    for i in range(-1, -len(contents), -1):
        update(data[i - 1], data[i], "ROOT")
    return data[0]


if __name__ == '__main__':  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputs", nargs='+', type=str, help="<Required> List of input yaml files.",
                        required=True)
    parser.add_argument("-o", "--output", type=str, help="Path to the output file, or stdout by default.")
    parser.add_argument("--indent", type=int, help="Number of space(s) for each indent.", default=2)

    args = parser.parse_args()

    file_contents = []
    for f in args.inputs:
        file_content = open(f, "r").read()
        file_contents.append(file_content)

    out_content = merge_yaml(file_contents)
    output = open(args.output, "w") if args.output else sys.stdout

    ruamel.yaml.round_trip_dump(out_content, output, indent=args.indent)
