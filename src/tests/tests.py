import sys
import unittest

from ruamel.yaml import YAML
from ruamel.yaml import round_trip_load
from ruamel.yaml.compat import StringIO

sys.path.append('..')
import yaml_tools


class MyYAML(YAML):
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


class TestCommands(unittest.TestCase):
    merge_str_out = """
        #comment1
        test:
          #ninja-comment2
          foo: 2 #comment1
          bar: 3 #comment3
          foobar: 3 #comment3
          #ninja-comment3
        """

    def test_unrecognized_command(self):
        sys.argv = ['yaml-tools', 'super-unrecognized-command-wtf']
        with self.assertRaises(SystemExit) as cm:
            yaml_tools.main()
        self.assertEqual(cm.exception.code, 1)

    def test_fail_delete_command(self):
        fi = './delete/file.yml'

        sys.argv = ['yaml-tools', 'delete', 'unknownKey0', '-i', fi]
        self.assertRaises(KeyError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'unknownKey1', 'foo', '-i', fi]
        self.assertRaises(RuntimeError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'test', 'foo', '0', 'check', '-i', fi]
        self.assertRaises(RuntimeError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'test', 'foo', 'h', '10' 'check', '-i', fi]
        self.assertRaises(RuntimeError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'test', 'foo', 'h', '1000', '-i', fi]
        self.assertRaises(RuntimeError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete',
                    'test', 'foo', 'unknownKey2', '0', '-i', fi]
        self.assertRaises(RuntimeError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete',
                    'test', 'foo', 'h', '2', 'unknownKey3', '-i', fi]
        self.assertRaises(KeyError, yaml_tools.main)

    def test_3_str_merge_with_comment(self):
        str1 = """
        #comment1
        test:
          foo: 1 #comment1
          #ninja-comment1
          bar: 1
        """
        str2 = """
        test:
          #ninja-comment2
          foo: 2
        """
        str3 = """
        test:
          bar: 3 #comment3
          foobar: 3 #comment3
          #ninja-comment3
        """

        out = yaml_tools.successive_merge([str1, str2, str3])
        expected_out = round_trip_load(self.merge_str_out)

        yml = MyYAML()
        out_str = yml.dump(out)
        expected_out_str = yml.dump(expected_out)
        self.assertEqual(out_str, expected_out_str)

    def test_3_files_merge_with_comment(self):
        f1 = './merge/file1.yml'
        f2 = './merge/file2.yml'
        f3 = './merge/file3.yml'
        fo = './merge/out.yml'
        feo = './merge/expected_out.yml'

        sys.argv = ['yaml-tools', 'merge', '-i', f1, f2, f3, '-o', fo]
        yaml_tools.main()

        out_file = open(fo, 'r')
        expected_out_file = open(feo, 'r')
        self.assertEqual(out_file.read(), expected_out_file.read())
        out_file.close()
        expected_out_file.close()

    def test_delete_item(self):
        fi = './delete/file.yml'
        fo = './delete/out.yml'
        feo = './delete/expected_out.yml'

        sys.argv = ['yaml-tools', 'delete',
                    'test', 'foo', 'h', '2', 'check', '-i', fi, '-o', fo]
        yaml_tools.main()

        sys.argv = ['yaml-tools', 'delete',
                    'test', 'foo', 'h', '2', 'ef', '-i', fo, '-o', fo]
        yaml_tools.main()

        sys.argv = ['yaml-tools', 'delete',
                    'test', 'foo', 'h', '1', 'check', '-i', fo, '-o', fo]
        yaml_tools.main()

        out_file = open(fo, 'r')
        expected_out_file = open(feo, 'r')
        self.assertEqual(out_file.read(), expected_out_file.read())
        out_file.close()
        expected_out_file.close()


class TestCommentCommand(unittest.TestCase):
    def test_comment_commented_map_item(self):
        str = """
#comment1
test:
  #ninja-comment
  foo:
    sub-foo: 1
  bar:
    sub-bar: 2
  baz:
    sub-baz: 3
            """
        expected_str = """
#comment1
test:
  #ninja-comment
  foo:
    sub-foo: 1
  #bar:
  #  sub-bar: 2
  baz:
    sub-baz: 3
            """

        data = round_trip_load(str, preserve_quotes=True)
        path_to_key = ['test', 'bar']
        out = yaml_tools.comment_yaml_item(data, path_to_key, False)
        expected_out = round_trip_load(expected_str, preserve_quotes=True)

        yml = MyYAML()
        out_str = yml.dump(out)
        expected_out_str = yml.dump(expected_out)
        self.assertEqual(out_str, expected_out_str)

    def test_comment_commented_seq_item(self):
        str = """
#comment1
test:
#ninja-comment
- foo:
  sub-foo: 1
- bar:
  sub-bar: 2
- baz:
  sub-baz: 3
            """
        expected_str = """
#comment1
test:
#ninja-comment
- foo:
  sub-foo: 1
#- bar:
#  sub-bar: 2
- baz:
  sub-baz: 3
            """

        data = round_trip_load(str, preserve_quotes=True)
        path_to_key = ['test', '1']
        out = yaml_tools.comment_yaml_item(data, path_to_key, True)
        expected_out = round_trip_load(expected_str, preserve_quotes=True)

        yml = MyYAML()
        out_str = yml.dump(out)
        expected_out_str = yml.dump(expected_out)
        self.assertEqual(out_str, expected_out_str)

    def test_fail_comment_commented(self):
        str = """
test:
  foo:
    sub-foo: 1
  bar:
  - sub-bar: 1
  - sub-bar: 2
            """
        data = round_trip_load(str, preserve_quotes=True)
        self.assertRaises(KeyError, yaml_tools.comment_yaml_item, data, ['unknown-key'])
        self.assertRaises(RuntimeError, yaml_tools.comment_yaml_item, data, ['test', 'bar', '1000'])
        self.assertRaises(RuntimeError, yaml_tools.comment_yaml_item, data, ['test', 'bar', 'NotAnInteger'])


class TestMergeByType(unittest.TestCase):
    mock_scalar_1 = 'test: 1'
    mock_scalar_2 = 'test: 2'
    mock_dict_1 = """
    test:
      foo: 1
      bar: 2
    """
    mock_dict_2 = """
    test:
      foobar: babar
    """
    mock_list_1 = """
    test:
      - item1
      - item2
    """
    mock_list_2 = """
    test:
      - item3
    """
    mock_None = ''

    # from scalar to any

    def test_merge_scalar_to_scalar(self):
        out = yaml_tools.successive_merge(
            [self.mock_scalar_1, self.mock_scalar_2])
        expected_out = round_trip_load(self.mock_scalar_2)
        self.assertEqual(out, expected_out)

    def test_merge_scalar_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [
            self.mock_dict_1, self.mock_scalar_2])

    def test_merge_scalar_to_list(self):
        out = yaml_tools.successive_merge(
            [self.mock_list_1, self.mock_scalar_2])
        expected_out_str = """
        test:
          - item1
          - item2
          - 2
        """
        expected_out = round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_scalar_to_None(self):
        out = yaml_tools.successive_merge([self.mock_None, self.mock_scalar_2])
        expected_out = round_trip_load(self.mock_scalar_2)
        self.assertEqual(out, expected_out)

    # from dict to any

    def test_merge_dict_to_scalar(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [
            self.mock_scalar_1, self.mock_dict_2])

    def test_merge_dict_to_dict(self):
        out = yaml_tools.successive_merge([self.mock_dict_1, self.mock_dict_2])
        expected_out_str = """
        test:
          foo: 1
          bar: 2
          foobar: babar
        """
        expected_out = round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_dict_to_list(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [
            self.mock_list_1, self.mock_dict_2])

    def test_merge_dict_to_None(self):
        out = yaml_tools.successive_merge([self.mock_None, self.mock_dict_2])
        expected_out = round_trip_load(self.mock_dict_2)
        self.assertEqual(out, expected_out)

    # from list to any

    def test_merge_list_to_scalar(self):
        out = yaml_tools.successive_merge(
            [self.mock_scalar_1, self.mock_list_2])
        expected_out_str = """
        test:
        - item3
        - 1
        """  # the scalar is appended at the end of the list
        expected_out = round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_list_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [
            self.mock_dict_1, self.mock_list_2])

    def test_merge_list_to_list(self):
        out = yaml_tools.successive_merge([self.mock_list_1, self.mock_list_2])
        expected_out_str = """
        test:
        - item1
        - item2
        - item3
        """
        expected_out = round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_list_to_None(self):
        out = yaml_tools.successive_merge(['test: ', self.mock_list_2])
        expected_out = round_trip_load(self.mock_list_2)
        self.assertEqual(out, expected_out)

    # from None to any
    def test_merge_None_to_any(self):
        out = yaml_tools.successive_merge([self.mock_None, self.mock_None])
        expected_out = round_trip_load(self.mock_None)
        self.assertEqual(out, expected_out,
                         'Merge None to None should succeed')
        out = yaml_tools.successive_merge([self.mock_scalar_1, self.mock_None])
        expected_out = round_trip_load(self.mock_scalar_1)
        self.assertEqual(out, expected_out,
                         'Merge None to scalar should succeed')
        out = yaml_tools.successive_merge([self.mock_dict_1, self.mock_None])
        expected_out = round_trip_load(self.mock_dict_1)
        self.assertEqual(out, expected_out,
                         'Merge None to dict should succeed')
        out = yaml_tools.successive_merge([self.mock_list_1, self.mock_None])
        expected_out = round_trip_load(self.mock_list_1)
        self.assertEqual(out, expected_out,
                         'Merge None to list should succeed')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
