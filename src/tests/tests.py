import unittest
import ruamel.yaml

import sys
sys.path.append('..')
import yaml_tools


class TestMerge(unittest.TestCase):
    def test_triple_merge_with_comment(self):
        file_1 = """
        #comment1
        test:
          foo: 1 #comment1
          bar: 1
        """
        file_2 = """
        test:
          foo: 2
        """
        file_3 = """
        test:
          bar: 3 #comment3
          foobar: 3 #comment3
        """
        out = yaml_tools.merge_yaml([file_1, file_2, file_3])
        # comment1 has been deleted (overwritten)
        expected_out_str = """
        #comment1
        test:
          foo: 2
          bar: 3 #comment3
          foobar: 3 #comment3
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
        expected_out = ruamel.yaml.round_trip_load(self.mock_scalar_2)
        self.assertNotEqual(out, expected_out)

    def test_merge_scalar_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_dict_1, self.mock_scalar_2])

    def test_merge_scalar_to_list(self):
        out = yaml_tools.merge_yaml([self.mock_list_1, self.mock_scalar_2])
        expected_out_str = """
        test:
          - item1
          - item2
          - 2
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_dict_to_scalar(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_scalar_1, self.mock_dict_2])

    def test_merge_dict_to_dict(self):
        out = yaml_tools.merge_yaml([self.mock_dict_1, self.mock_dict_2])
        expected_out_str = """
        test:
          foo: 1
          bar: 2
          foobar: babar
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_dict_to_list(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_list_1, self.mock_dict_2])

    def test_merge_list_to_scalar(self):
        out = yaml_tools.merge_yaml([self.mock_scalar_1, self.mock_list_2])
        expected_out_str = """
        test:
        - item3
        - 1
        """  # the scalar is appended at the end of the list
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)

    def test_merge_list_to_dict(self):
        self.assertRaises(TypeError, yaml_tools.merge_yaml, [self.mock_dict_1, self.mock_list_2])

    def test_merge_list_to_list(self):
        out = yaml_tools.merge_yaml([self.mock_list_1, self.mock_list_2])
        expected_out_str = """
        test:
        - item1
        - item2
        - item3
        """
        expected_out = ruamel.yaml.round_trip_load(expected_out_str)
        self.assertEqual(out, expected_out)


if __name__ == '__main__':
    unittest.main()
