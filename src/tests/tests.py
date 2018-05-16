import unittest
import ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

import sys
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
          foo: 2 #comment1
          bar: 3 #comment3
          foobar: 3 #comment3
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

        sys.argv = ['yaml-tools', 'delete', 'test.foo[0]', '-i', fi]
        self.assertRaises(KeyError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'test.foo.h[1000]', '-i', fi]
        self.assertRaises(IndexError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'test.foo.unknownKey1[0]', '-i', fi]
        self.assertRaises(KeyError, yaml_tools.main)

        sys.argv = ['yaml-tools', 'delete', 'test.foo.h[2].unknownKey2', '-i', fi]
        self.assertRaises(TypeError, yaml_tools.main)

    def test_3_str_merge_with_comment(self):
        str1 = """
        #comment1
        test:
          foo: 1 #comment1
          bar: 1
        """
        str2 = """
        test:
          foo: 2
        """
        str3 = """
        test:
          bar: 3 #comment3
          foobar: 3 #comment3
        """

        out = yaml_tools.successive_merge([str1, str2, str3])
        expected_out = ruamel.yaml.round_trip_load(self.merge_str_out)

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

        sys.argv = ['yaml-tools', 'delete', 'test.foo.h[2]', '-i', fi, '-o', fo]
        yaml_tools.main()
        sys.argv = ['yaml-tools', 'delete', 'test.foo.h[1].check', '-i', fo, '-o', fo]
        yaml_tools.main()

        out_file = open(fo, 'r')
        expected_out_file = open(feo, 'r')
        self.assertEqual(out_file.read(), expected_out_file.read())
        out_file.close()
        expected_out_file.close()


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

    def test_merge_scalar_to_scalar(self):
        out = yaml_tools.successive_merge([self.mock_scalar_1, self.mock_scalar_2])
        expected_out = ruamel.yaml.round_trip_load(self.mock_scalar_2)
        self.assertEqual(out, expected_out)

    def test_merge_scalar_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [self.mock_dict_1, self.mock_scalar_2])

    def test_merge_scalar_to_list(self):
        out = yaml_tools.successive_merge([self.mock_list_1, self.mock_scalar_2])
        expected_out_str = """
        test:
          - item1
          - item2
          - 2
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_dict_to_scalar(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [self.mock_scalar_1, self.mock_dict_2])

    def test_merge_dict_to_dict(self):
        out = yaml_tools.successive_merge([self.mock_dict_1, self.mock_dict_2])
        expected_out_str = """
        test:
          foo: 1
          bar: 2
          foobar: babar
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_dict_to_list(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [self.mock_list_1, self.mock_dict_2])

    def test_merge_list_to_scalar(self):
        out = yaml_tools.successive_merge([self.mock_scalar_1, self.mock_list_2])
        expected_out_str = """
        test:
        - item3
        - 1
        """  # the scalar is appended at the end of the list
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_list_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.successive_merge, [self.mock_dict_1, self.mock_list_2])

    def test_merge_list_to_list(self):
        out = yaml_tools.successive_merge([self.mock_list_1, self.mock_list_2])
        expected_out_str = """
        test:
        - item1
        - item2
        - item3
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
