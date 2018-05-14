import argparse
import ruamel.yaml


def update(d, n):  # data, new_data
    print("???")
    if isinstance(n, ruamel.yaml.comments.CommentedMap):
        for k in n:
            d[k] = update(d[k], n[k]) if k in d else n[k]
            if k in n.ca._items and n.ca._items[k][2] and \
                    n.ca._items[k][2].value.strip():
                d.ca._items[k] = n.ca._items[k]  # copy non-empty comment
    else:
        d = n
    return d


def move_comment(d, depth=0, indent=2):
    # recursively adjust comment
    if isinstance(d, ruamel.yaml.comments.CommentedMap):
        for k in d:
            if isinstance(d[k], ruamel.yaml.comments.CommentedMap):
                if hasattr(d, 'ca'):
                    comment = d.ca.items.get(k)
                    if comment and comment[3] is not None:
                        # add to first key of the mapping that is the value
                        for k1 in d[k]:
                            d[k].yaml_set_comment_before_after_key(
                                k1,
                                before=comment[3][0].value.lstrip('#').strip(),
                                indent=indent * (depth + 1))
                            break
            move_comment(d[k], depth + 1)
    return d


def main(args):
    data_list = []
    for f in args.inputs:
        file = open(f, "r")
        data = ruamel.yaml.round_trip_load(file)
        data_list.append(data)
    for i in range(-1, -len(data_list) + 1, -1):
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
