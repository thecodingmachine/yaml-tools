import unittest
import ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

import sys
sys.path.append('..')
import yaml_tools


class MyYAML(YAML):
    # dump add a '\n' at the end
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


class TestMerge(unittest.TestCase):
    def test_triple_merge_with_comment(self):
        file_1 = """
        #comment1
        test:
          foo: 1
          bar: 1
        """
        file_2 = """
        test:
          foo: 2 #comment2
        """
        file_3 = """
        test:
          bar: 3 #comment3
        """
        out = yaml_tools.merge_yaml([file_1, file_2, file_3])

        expected_out_str = """
        #comment1
        test:
          foo: 2 #comment2
          bar: 3 #comment3
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)

        self.assertEqual(out, expected_out)


class TestMergeByType(unittest.TestCase):
    mock_scalar_1 = "test: 1"
    mock_scalar_2 = "test: 2"
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
        out = yaml_tools.merge_yaml([self.mock_scalar_1, self.mock_scalar_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test: 2\n"  # the merge (the dump) add a '\n' at the end
        self.assertEqual(out_str, expected_out_str)

    def test_merge_scalar_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_dict_1, self.mock_scalar_2])

    def test_merge_scalar_to_list(self):
        out = yaml_tools.merge_yaml([self.mock_list_1, self.mock_scalar_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item1\n- item2\n- 2\n"  # the merge deletes indent before list items..
        self.assertEqual(out_str, expected_out_str)

    def test_merge_dict_to_scalar(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_scalar_1, self.mock_dict_2])

    def test_merge_dict_to_dict(self):
        out = yaml_tools.merge_yaml([self.mock_dict_1, self.mock_dict_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n  foo: 1\n  bar: 2\n  foobar: babar\n"
        self.assertEqual(out_str, expected_out_str)

    def test_merge_dict_to_list(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_list_1, self.mock_dict_2])

    def test_merge_list_to_scalar(self):
        out = yaml_tools.merge_yaml([self.mock_scalar_1, self.mock_list_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item3\n- 1\n"  # the scalar is appended at the end of the list
        self.assertEqual(out_str, expected_out_str)

    def test_merge_list_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_dict_1, self.mock_list_2])

    def test_merge_list_to_list(self):
        out = yaml_tools.merge_yaml([self.mock_list_1, self.mock_list_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item1\n- item2\n- item3\n"
        self.assertEqual(out_str, expected_out_str)


if __name__ == '__main__':
    unittest.main()
