# Copyright (c) 2016 Cyso < development [at] cyso . com >
#
# This file is part of omniconf, a.k.a. python-omniconf .
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see
# <http://www.gnu.org/licenses/>.

import unittest
from omniconf.config import ConfigRegistry, config, DEFAULT_REGISTRY, SETTING_REGISTRY
from omniconf.exceptions import UnknownSettingError, UnconfiguredSettingError
from omniconf.setting import SettingRegistry, Setting
from mock import Mock, call
import nose.tools


class TestConfigRegistry(unittest.TestCase):
    def setUp(self):
        self.setting_registry = SettingRegistry()
        self.setting_registry.add(Setting("key", _type=str, required=True))
        self.setting_registry.add(Setting("default", _type=str, default="present"))
        self.config_registry = ConfigRegistry(setting_registry=self.setting_registry)

    def test_config_registry_set_without_setting(self):
        with self.assertRaises(UnknownSettingError):
            self.config_registry.set("nope", "value")

    def test_config_registry_set_with_setting(self):
        self.config_registry.set("key", "value")
        self.assertEqual(self.config_registry.registry['key'], "value")

    def test_config_registry_has(self):
        self.assertFalse(self.config_registry.has("key"))
        self.config_registry.set("key", "added")
        self.assertTrue(self.config_registry.has("key"))

    def test_config_registry_has_with_default(self):
        self.assertTrue(self.config_registry.has("default"))

    def test_config_registry_get_without_config(self):
        with self.assertRaises(UnconfiguredSettingError):
            self.config_registry.get("nope")

    def test_config_registry_get(self):
        self.config_registry.set("key", "value")
        self.assertEqual(self.config_registry.get("key"), "value")

    def test_config_registry_get_with_default(self):
        self.assertEqual(self.config_registry.get("default"), "present")

    def test_config_registry_get_not_required_no_value(self):
        self.setting_registry.add(Setting("unneeded", _type=str))
        self.assertIs(self.config_registry.get("unneeded"), None)

    def test_config_registry_list(self):
        self.assertEqual(self.config_registry.list(), self.config_registry.registry)

    def test_config_registry_unset(self):
        self.config_registry.set("key", "soon")
        self.assertEqual(self.config_registry.get("key"), "soon")
        self.config_registry.unset("key")
        with self.assertRaises(UnconfiguredSettingError):
            self.config_registry.get("key")

    def test_config_registry_load(self):
        mock_backend = Mock()
        mock_backend.get_value.return_value = "value"
        self.config_registry.load([mock_backend])

        mock_backend.get_value.assert_has_calls([call("key"), call("default")], any_order=True)
        self.assertEqual(self.config_registry.get("key"), "value")
        self.assertEqual(self.config_registry.get("default"), "value")

    def test_config_registry_load_with_previous_values(self):
        mock_backend = Mock()
        mock_backend.get_value.return_value = "value"
        self.config_registry.set("key", "other")
        self.config_registry.set("default", "other")

        self.config_registry.load([mock_backend])

        self.assertEqual(self.config_registry.get("key"), "other")
        self.assertEqual(self.config_registry.get("default"), "other")

    def test_config_registry_load_with_unavailable_values(self):
        mock_backend = Mock()
        mock_backend.get_value.side_effect = KeyError("No value")

        with self.assertRaises(UnconfiguredSettingError):
            self.config_registry.load([mock_backend])


class TestConfigMethod(unittest.TestCase):
    def setUp(self):
        self.setting_registry = SettingRegistry()
        self.setting_registry.add(Setting("key", _type=str, required=True))
        self.setting_registry.add(Setting("default", _type=str, default="present"))
        self.config_registry = ConfigRegistry(setting_registry=self.setting_registry)

    def test_config_method_without_config(self):
        with self.assertRaises(UnconfiguredSettingError):
            config("key", registry=self.config_registry)

    def test_config_method(self):
        self.config_registry.set("key", "value")
        self.assertEqual(config("key", registry=self.config_registry), "value")

    def test_config_method_with_default(self):
        self.assertEqual(config("default", registry=self.config_registry), "present")

    def test_config_method_with_default_registry(self):
        with self.assertRaises(UnconfiguredSettingError):
            config("foo")

        _setting = Setting(key="foo", _type=str)
        SETTING_REGISTRY.add(_setting)
        DEFAULT_REGISTRY.set("foo", "bar")
        self.assertEqual(config("foo"), "bar")

        DEFAULT_REGISTRY.unset("foo")
        SETTING_REGISTRY.remove(_setting)

VALUE_TESTS = [
    ("foobar", "foobar", str),
    ("1234", 1234, int),
    ("123.456", 123.456, float),
    ("['a', 'b', '1', 'c']", ['a', 'b', '1', 'c'], list),
    ("('a', 'b', '1', 'c')", ('a', 'b', '1', 'c'), tuple),
    ("{'a': 'b', 'foo': 'bar'}", {'a': 'b', 'foo': 'bar'}, dict),
    ("False", False, bool),
    ("True", True, bool),
    (False, False, bool),
]


def test_config_registry_set_value_conversion():
    for _in, _out, _type in VALUE_TESTS:
        yield _test_set_value, _in, _out, _type


def _test_set_value(_in, _out, _type):
    settings = SettingRegistry()
    settings.add(Setting("test.value", _type=_type))

    configs = ConfigRegistry(setting_registry=settings)
    configs.set("test.value", _in)

    nose.tools.assert_equal(configs.get("test.value"), _out)
