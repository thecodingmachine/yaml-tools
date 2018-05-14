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
    mock_scalar_1 = "test"
    mock_scalar_2 = "test2"
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
        expected_out_str = "test2\n"  # the merge (the dump) add a '\n' at the end
        self.assertEqual(out_str, expected_out_str)

    def test_merge_scalar_to_dict(self):
        import yaml_tools
        dest = """
        test:
          foo: 1
          bar: 2
        """
        source = "test"
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [dest, source])

    def test_merge_scalar_to_list(self):
        import yaml_tools
        dest = "test:\n  - item1\n  - item2"
        source = "test: scalar"
        out = yaml_tools.merge_yaml([dest, source])
        yaml = MyYAML()
        out_str = yaml.dump(out)
        expected_out_str = "test:\n- item1\n- item2\n- scalar\n"  # the merge deletes indent before list items
        self.assertEqual(out_str, expected_out_str)

    def test_merge_dict_to_scalar(self):
        import yaml_tools
        source = "test: 1"
        dest = "test"
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [dest, source])

    def test_merge_dict_to_list(self):
        import yaml_tools
        dest = "test:\n  - item1\n  - item2"
        source = """
        test:
          foo: 1
          bar: 2
        """
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [dest, source])

if __name__ == '__main__':
    unittest.main()
