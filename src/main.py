import argparse
import ruamel.yaml


def get_type_error(dest, src):
    return TypeError("Error trying to merge a {0} in a {1}".format(type(src), type(dest)))


def update(dest, src):
    if isinstance(src, ruamel.yaml.comments.CommentedMap):
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            for k in src:
                dest[k] = update(dest[k], src[k]) if k in dest else src[k]
                if k in src.ca._items and src.ca._items[k][2] and \
                        src.ca._items[k][2].value.strip():
                    dest.ca._items[k] = src.ca._items[k]  # copy non-empty comment
        else:
            raise get_type_error(dest, src)
    elif isinstance(src, ruamel.yaml.comments.CommentedSeq):
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            raise get_type_error(dest, src)
        elif isinstance(dest, ruamel.yaml.comments.CommentedSeq):
            dest.extend(src)
        else:
            src.append(dest)
            dest = src
    else:
        if isinstance(dest, ruamel.yaml.comments.CommentedMap):
            raise get_type_error(dest, src)
        elif isinstance(dest, ruamel.yaml.comments.CommentedSeq):
            dest.append(src)
        else:
            dest = src
    return dest


def move_comment(dest, depth=0, indent=2):
    # recursively adjust comment
    if isinstance(dest, ruamel.yaml.comments.CommentedMap):
        for k in dest:
            if isinstance(dest[k], ruamel.yaml.comments.CommentedMap):
                if hasattr(dest, 'ca'):
                    comment = dest.ca.items.get(k)
                    if comment and comment[3] is not None:
                        # add to first key of the mapping that is the value
                        for k1 in dest[k]:
                            dest[k].yaml_set_comment_before_after_key(
                                k1,
                                before=comment[3][0].value.lstrip('#').strip(),
                                indent=indent * (depth + 1))
                            break
            move_comment(dest[k], depth + 1)
    return dest


def main(args):
    data_list = []
    for f in args.inputs:
        file_content = open(f, "r").read()
        data = ruamel.yaml.round_trip_load(file_content)
        data_list.append(data)
    for i in range(-1, -len(data_list), -1):
        update(data_list[i - 1], move_comment(data_list[i]))

    output_file = open(args.output, "w")
    ruamel.yaml.round_trip_dump(data_list[0], output_file, indent=args.indent)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputs", nargs='+', type=str, help="<Required> List of input yaml files",
                        required=True)
    parser.add_argument("-o", "--output", type=str, help="Path to the output file", default="./output.yaml")
    parser.add_argument("--indent", type=int, help="Number of space(s) for each indent", default=2)

    arguments = parser.parse_args()
    main(arguments)
