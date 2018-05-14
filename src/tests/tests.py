import unittest
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import sys

sys.path.append('..')


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


class TestMergeBasic(unittest.TestCase):
    def test_basic_with_comment(self):
        import yaml_tools
        dest = "#comment 1\ntest: 1"
        source = "test: 2"
        source2 = "test: 3 #comment 3"
        out = yaml_tools.merge_yaml([dest, source, source2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "#comment 1\ntest: 3 #comment 3\n"
        self.assertEqual(out_str, expected_out_str)


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
        import yaml_tools
        out = yaml_tools.merge_yaml([self.mock_scalar_1, self.mock_scalar_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test: 2\n"  # the merge (the dump) add a '\n' at the end
        self.assertEqual(out_str, expected_out_str)

    def test_merge_scalar_to_dict(self):
        import yaml_tools
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_dict_1, self.mock_scalar_2])

    def test_merge_scalar_to_list(self):
        import yaml_tools
        out = yaml_tools.merge_yaml([self.mock_list_1, self.mock_scalar_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item1\n- item2\n- 2\n"  # the merge deletes indent before list items..
        self.assertEqual(out_str, expected_out_str)

    def test_merge_dict_to_scalar(self):
        import yaml_tools
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_scalar_1, self.mock_dict_2])

    def test_merge_dict_to_dict(self):
        import yaml_tools
        out = yaml_tools.merge_yaml([self.mock_dict_1, self.mock_dict_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n  foo: 1\n  bar: 2\n  foobar: babar\n"
        self.assertEqual(out_str, expected_out_str)

    def test_merge_dict_to_list(self):
        import yaml_tools
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_list_1, self.mock_dict_2])

    def test_merge_list_to_scalar(self):
        import yaml_tools
        out = yaml_tools.merge_yaml([self.mock_scalar_1, self.mock_list_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item3\n- 1\n"  # the scalar is appended at the end of the list
        self.assertEqual(out_str, expected_out_str)

    def test_merge_list_to_dict(self):
        import yaml_tools
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_dict_1, self.mock_list_2])

    def test_merge_list_to_list(self):
        import yaml_tools
        out = yaml_tools.merge_yaml([self.mock_list_1, self.mock_list_2])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item1\n- item2\n- item3\n"
        self.assertEqual(out_str, expected_out_str)


if __name__ == '__main__':
    unittest.main()
