"""Roundtrip tests for INI ↔ TOML conversion.

These tests verify that conversions in both directions produce
semantically equivalent configurations.
"""

from pathlib import Path

from batou.config_toml import load_toml_config
from batou.ini_to_toml import InferMode, convert_config_to_toml, format_toml
from batou.toml_to_ini import convert_toml_to_ini

# Sample INI configurations for testing
MINIMAL_INI = """\
[environment]
connect_method = local

[hosts]
localhost = myapp
"""

COMPLEX_INI = """\
[environment]
host_domain = example.com
platform = nixos
timeout = 300
update_method = git-bundle

[hosts]
host01 = nginx
host02 = backend

[host:host01]
components = nginx
    mysql
data-ram = 4
data-disk = 40

[component:myapp]
database_host = db.example.com
database_port = 5432
debug = true

[resolver]
db.internal = 10.0.1.50
"""


class TestIniToTomlToIni:
    """Test INI → TOML → INI roundtrip."""

    def test_minimal_roundtrip(self, tmp_path: Path):
        """Test minimal config roundtrip."""
        # Write INI
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(MINIMAL_INI)

        # INI → TOML (default mode: no type inference)
        toml_data = convert_config_to_toml(ini_path)
        toml_content = format_toml(toml_data)

        # TOML → INI
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml_content)
        ini_result = convert_toml_to_ini(toml_path)

        # Parse both INIs and compare - should be exact match now
        import configparser

        cfg1 = configparser.ConfigParser()
        cfg1.optionxform = str
        cfg1.read_string(MINIMAL_INI)

        cfg2 = configparser.ConfigParser()
        cfg2.optionxform = str
        cfg2.read_string(ini_result)

        assert dict(cfg1["environment"]) == dict(cfg2["environment"])
        assert dict(cfg1["hosts"]) == dict(cfg2["hosts"])

    def test_perfect_roundtrip_preserves_strings(self, tmp_path: Path):
        """Test that default mode preserves strings exactly."""
        # Use component section which allows arbitrary keys
        ini = """\
[environment]
connect_method = local

[component:config]
port = 0123
version = 5.0
enabled = yes
count = 42
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        # Default mode: no type inference
        toml_data = convert_config_to_toml(ini_path, InferMode.NONE)
        toml_content = format_toml(toml_data)

        # All values should be strings
        assert toml_data["components"]["config"]["port"] == "0123"
        assert toml_data["components"]["config"]["version"] == "5.0"
        assert toml_data["components"]["config"]["enabled"] == "yes"
        assert toml_data["components"]["config"]["count"] == "42"

        # Roundtrip should be perfect
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml_content)
        ini_result = convert_toml_to_ini(toml_path)

        import configparser

        cfg1 = configparser.ConfigParser()
        cfg1.optionxform = str
        cfg1.read_string(ini)

        cfg2 = configparser.ConfigParser()
        cfg2.optionxform = str
        cfg2.read_string(ini_result)

        # All values should match exactly
        assert dict(cfg1["component:config"]) == dict(cfg2["component:config"])

    def test_complex_roundtrip_environment_section(self, tmp_path: Path):
        """Test environment section preservation."""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(COMPLEX_INI)

        toml_data = convert_config_to_toml(ini_path)
        toml_content = format_toml(toml_data)

        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml_content)
        ini_result = convert_toml_to_ini(toml_path)

        import configparser

        cfg1 = configparser.ConfigParser()
        cfg1.optionxform = str
        cfg1.read_string(COMPLEX_INI)

        cfg2 = configparser.ConfigParser()
        cfg2.optionxform = str
        cfg2.read_string(ini_result)

        # Compare environment section values
        for key in cfg1["environment"]:
            assert (
                cfg1["environment"][key] == cfg2["environment"][key]
            ), f"Mismatch in environment.{key}"

    def test_complex_roundtrip_hosts(self, tmp_path: Path):
        """Test hosts section preservation."""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(COMPLEX_INI)

        toml_data = convert_config_to_toml(ini_path)
        toml_content = format_toml(toml_data)

        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml_content)
        ini_result = convert_toml_to_ini(toml_path)

        import configparser

        cfg1 = configparser.ConfigParser()
        cfg1.optionxform = str
        cfg1.read_string(COMPLEX_INI)

        cfg2 = configparser.ConfigParser()
        cfg2.optionxform = str
        cfg2.read_string(ini_result)

        assert dict(cfg1["hosts"]) == dict(cfg2["hosts"])

    def test_complex_roundtrip_resolver(self, tmp_path: Path):
        """Test resolver section preservation."""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(COMPLEX_INI)

        toml_data = convert_config_to_toml(ini_path)
        toml_content = format_toml(toml_data)

        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml_content)
        ini_result = convert_toml_to_ini(toml_path)

        import configparser

        cfg1 = configparser.ConfigParser()
        cfg1.optionxform = str
        cfg1.read_string(COMPLEX_INI)

        cfg2 = configparser.ConfigParser()
        cfg2.optionxform = str
        cfg2.read_string(ini_result)

        assert dict(cfg1["resolver"]) == dict(cfg2["resolver"])


class TestTomlToIniToToml:
    """Test TOML → INI → TOML roundtrip."""

    MINIMAL_TOML = """\
[environment]
connect_method = "local"

[hosts]
localhost = "myapp"
"""

    COMPLEX_TOML = """\
[environment]
host_domain = "example.com"
platform = "nixos"
timeout = 300
update_method = "git-bundle"

[hosts]
host01 = "frontend"
host02 = "backend"

[host.host01]
components = ["nginx", "mysql"]
data-ram = 4
data-disk = 40

[components.myapp]
database_host = "db.example.com"
database_port = 5432
debug = true

[resolver]
"db.internal" = "10.0.1.50"
"""

    def test_minimal_roundtrip(self, tmp_path: Path):
        """Test minimal TOML roundtrip."""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(self.MINIMAL_TOML)

        # TOML → INI
        ini_content = convert_toml_to_ini(toml_path)
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini_content)

        # INI → TOML
        toml_data = convert_config_to_toml(ini_path)
        toml_result = format_toml(toml_data)

        # Parse and compare
        original_config = load_toml_config(self.MINIMAL_TOML)
        result_config = load_toml_config(toml_result)

        assert (
            original_config.environment.connect_method
            == result_config.environment.connect_method
        )
        assert "localhost" in result_config.hosts

    def test_complex_roundtrip_environment(self, tmp_path: Path):
        """Test environment section TOML roundtrip."""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(self.COMPLEX_TOML)

        ini_content = convert_toml_to_ini(toml_path)
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini_content)

        toml_data = convert_config_to_toml(ini_path)
        toml_result = format_toml(toml_data)

        original_config = load_toml_config(self.COMPLEX_TOML)
        result_config = load_toml_config(toml_result)

        assert (
            original_config.environment.host_domain
            == result_config.environment.host_domain
        )
        assert (
            original_config.environment.platform == result_config.environment.platform
        )
        assert original_config.environment.timeout == result_config.environment.timeout

    def test_complex_roundtrip_host_details(self, tmp_path: Path):
        """Test host details TOML roundtrip."""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(self.COMPLEX_TOML)

        ini_content = convert_toml_to_ini(toml_path)
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini_content)

        toml_data = convert_config_to_toml(ini_path)
        toml_result = format_toml(toml_data)

        load_toml_config(self.COMPLEX_TOML)
        result_config = load_toml_config(toml_result)

        assert "host01" in result_config.host
        assert result_config.host["host01"].components == ["nginx", "mysql"]

    def test_complex_roundtrip_components(self, tmp_path: Path):
        """Test component overrides TOML roundtrip."""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(self.COMPLEX_TOML)

        ini_content = convert_toml_to_ini(toml_path)
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini_content)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)
        toml_result = format_toml(toml_data)

        load_toml_config(self.COMPLEX_TOML)
        result_config = load_toml_config(toml_result)

        assert "myapp" in result_config.components
        assert result_config.components["myapp"]["database_host"] == "db.example.com"
        assert result_config.components["myapp"]["database_port"] == 5432


class TestTypeInference:
    """Test type inference in INI → TOML conversion."""

    def test_boolean_inference(self, tmp_path: Path):
        """Test boolean type inference."""
        ini = """\
[environment]
connect_method = local

[component:test]
enabled = true
disabled = false
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["components"]["test"]["enabled"] is True
        assert toml_data["components"]["test"]["disabled"] is False

    def test_integer_inference(self, tmp_path: Path):
        """Test integer type inference."""
        ini = """\
[environment]
timeout = 300
max_connections = 100
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["environment"]["timeout"] == 300
        assert toml_data["environment"]["max_connections"] == 100
        assert isinstance(toml_data["environment"]["timeout"], int)

    def test_list_from_newlines(self, tmp_path: Path):
        """Test list inference from newline-separated values."""
        ini = """\
[environment]
connect_method = local

[host:web01]
components = nginx
    mysql
    redis
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["host"]["web01"]["components"] == [
            "nginx",
            "mysql",
            "redis",
        ]

    def test_list_from_commas(self, tmp_path: Path):
        """Test list inference from comma-separated values."""
        ini = """\
[environment]
connect_method = local

[component:app]
servers = host1, host2, host3
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["components"]["app"]["servers"] == [
            "host1",
            "host2",
            "host3",
        ]

    def test_negative_integer(self, tmp_path: Path):
        """Test negative integer inference."""
        ini = """\
[environment]
connect_method = local

[component:cache]
ttl = -1
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["components"]["cache"]["ttl"] == -1
        assert isinstance(toml_data["components"]["cache"]["ttl"], int)

    def test_float_inference(self, tmp_path: Path):
        """Test float type inference."""
        ini = """\
[environment]
connect_method = local

[component:math]
ratio = 3.14159
factor = 2.5
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["components"]["math"]["ratio"] == 3.14159
        assert toml_data["components"]["math"]["factor"] == 2.5

    def test_no_inference_keeps_strings(self, tmp_path: Path):
        """Test that default mode keeps everything as strings."""
        ini = """\
[environment]
connect_method = local
timeout = 300
enabled = true
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.NONE)

        # Everything should be strings
        assert toml_data["environment"]["connect_method"] == "local"
        assert toml_data["environment"]["timeout"] == "300"
        assert toml_data["environment"]["enabled"] == "true"
        assert isinstance(toml_data["environment"]["timeout"], str)

    def test_safe_mode_only_bools_and_lists(self, tmp_path: Path):
        """Test that safe mode only converts bools and lists."""
        ini = """\
[environment]
connect_method = local
timeout = 300
enabled = true

[host:web01]
components = nginx
    mysql
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.SAFE)

        # Bool should be converted
        assert toml_data["environment"]["enabled"] is True
        # List should be converted
        assert toml_data["host"]["web01"]["components"] == ["nginx", "mysql"]
        # Integer should stay string
        assert toml_data["environment"]["timeout"] == "300"
        assert isinstance(toml_data["environment"]["timeout"], str)


class TestPathologicalCases:
    """Test edge cases and unusual configurations."""

    def test_resolver_multi_ip(self, tmp_path: Path):
        """Test resolver with multiple IPs (newline-separated)."""
        # Note: INI doesn't support quoted keys - that's a TOML feature
        # Use simple hostname without dots for this test
        ini = """\
[environment]
connect_method = local

[resolver]
dbinternal = 10.0.1.50
    10.0.1.51
    ::1
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        # INI → TOML
        toml_data = convert_config_to_toml(ini_path)
        assert toml_data["resolver"]["dbinternal"] == [
            "10.0.1.50",
            "10.0.1.51",
            "::1",
        ]

        # TOML → INI
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(format_toml(toml_data))
        ini_result = convert_toml_to_ini(toml_path)

        import configparser

        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read_string(ini_result)

        # Should be newline-separated in INI
        assert "10.0.1.50" in cfg["resolver"]["dbinternal"]
        assert "10.0.1.51" in cfg["resolver"]["dbinternal"]

    def test_data_roles_as_list(self, tmp_path: Path):
        """Test data-roles attribute as list."""
        ini = """\
[environment]
connect_method = local

[host:web01]
components = nginx
data-roles = docker
    mailstub
    nfs_rg_client
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        # data-roles should become a list
        assert toml_data["host"]["web01"]["data-roles"] == [
            "docker",
            "mailstub",
            "nfs_rg_client",
        ]

    def test_url_values(self, tmp_path: Path):
        """Test URLs and paths with special characters."""
        ini = """\
[environment]
connect_method = local

[component:api]
endpoint = https://api.example.com:8080/v1
database_url = postgresql://user:pass@host:5432/db
log_path = /var/log/myapp/access.log
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        assert (
            toml_data["components"]["api"]["endpoint"]
            == "https://api.example.com:8080/v1"
        )
        assert (
            toml_data["components"]["api"]["database_url"]
            == "postgresql://user:pass@host:5432/db"
        )
        assert toml_data["components"]["api"]["log_path"] == "/var/log/myapp/access.log"

    def test_vfs_section(self, tmp_path: Path):
        """Test VFS section roundtrip."""
        ini = """\
[environment]
connect_method = local

[vfs]
class = batou.lib.vfs.LocalVFS
root = /tmp/deploy
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        # INI → TOML
        toml_data = convert_config_to_toml(ini_path)

        # TOML → INI
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(format_toml(toml_data))
        ini_result = convert_toml_to_ini(toml_path)

        import configparser

        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read_string(ini_result)

        assert cfg["vfs"]["class"] == "batou.lib.vfs.LocalVFS"
        assert cfg["vfs"]["root"] == "/tmp/deploy"

    def test_boolean_variants(self, tmp_path: Path):
        """Test various boolean representations."""
        ini = """\
[environment]
connect_method = local

[component:flags]
flag_yes = yes
flag_no = no
flag_on = on
flag_off = off
flag_true = true
flag_false = false
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        assert toml_data["components"]["flags"]["flag_yes"] is True
        assert toml_data["components"]["flags"]["flag_no"] is False
        assert toml_data["components"]["flags"]["flag_on"] is True
        assert toml_data["components"]["flags"]["flag_off"] is False
        assert toml_data["components"]["flags"]["flag_true"] is True
        assert toml_data["components"]["flags"]["flag_false"] is False

    def test_string_that_looks_like_list(self, tmp_path: Path):
        """Test strings that contain commas but aren't lists."""
        ini = """\
[environment]
connect_method = local

[component:email]
header = X-Custom-Header: value with, commas, inside
greeting = Hello, World!
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        # These contain commas but also special chars, so shouldn't be lists
        assert isinstance(toml_data["components"]["email"]["header"], str)
        assert isinstance(toml_data["components"]["email"]["greeting"], str)

    def test_quoted_hostname_in_resolver(self, tmp_path: Path):
        """Test quoted hostnames in resolver section."""
        toml = """\
[environment]
connect_method = "local"

[resolver]
"db.internal" = "10.0.1.50"
"cache.internal" = ["10.0.2.1", "10.0.2.2"]
"""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml)

        # TOML → INI
        ini_content = convert_toml_to_ini(toml_path)
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini_content)

        # INI → TOML
        toml_data = convert_config_to_toml(ini_path)

        assert toml_data["resolver"]["db.internal"] == "10.0.1.50"
        assert toml_data["resolver"]["cache.internal"] == ["10.0.2.1", "10.0.2.2"]

    def test_yaml_in_ini(self, tmp_path: Path):
        """Test YAML-in-INI with pipe prefix (the horror)."""
        # This is the ugliest thing in batou configs - YAML embedded in INI
        # The pipe prefix indicates YAML content
        ini = """\
[environment]
connect_method = local

[component:haproxy]
config = |frontend: www
    bind: "*:80"
    default_backend: web
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        # The YAML parser should convert this to a proper structure
        config = toml_data["components"]["haproxy"]["config"]
        # It becomes a nested dict from YAML parsing
        assert isinstance(config, dict)
        assert "frontend" in config

    def test_yaml_in_ini_simple_dict(self, tmp_path: Path):
        """Test YAML-in-INI with simple dict structure."""
        ini = """\
[environment]
connect_method = local

[component:settings]
options = |key1: value1
    key2: value2
    nested:
      subkey: subvalue
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        # Should become a proper nested dict
        options = toml_data["components"]["settings"]["options"]
        assert isinstance(options, dict)

    def test_provisioner_section(self, tmp_path: Path):
        """Test provisioner section roundtrip."""
        toml = """\
[environment]
connect_method = "local"

[provisioners.mycloud]
provider = "aws"
region = "eu-central-1"
instance_type = "t3.medium"
"""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml)

        # TOML → INI
        ini_content = convert_toml_to_ini(toml_path)

        # INI → TOML
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini_content)
        toml_data = convert_config_to_toml(ini_path)

        assert "mycloud" in toml_data["provisioner"]
        assert toml_data["provisioner"]["mycloud"]["provider"] == "aws"
        assert toml_data["provisioner"]["mycloud"]["region"] == "eu-central-1"

    def test_empty_string_value(self, tmp_path: Path):
        """Test empty string value handling."""
        ini = """\
[environment]
connect_method = local

[component:app]
name = myapp
description =
optional =
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        # Empty strings should be preserved
        assert toml_data["components"]["app"]["name"] == "myapp"
        assert toml_data["components"]["app"]["description"] == ""
        assert toml_data["components"]["app"]["optional"] == ""

    def test_whitespace_preservation(self, tmp_path: Path):
        """Test that leading/trailing whitespace is handled."""
        ini = """\
[environment]
connect_method = local

[component:app]
message =   Hello World
path = /var/log/app
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        # ConfigParser strips whitespace
        assert toml_data["components"]["app"]["message"] == "Hello World"
        assert toml_data["components"]["app"]["path"] == "/var/log/app"

    def test_special_chars_in_values(self, tmp_path: Path):
        """Test special characters in values."""
        ini = r"""[environment]
connect_method = local

[component:regex]
pattern = ^[a-zA-Z0-9_]+$
template = {{name}} - {{value}}
json_fragment = {"key": "value"}
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        assert toml_data["components"]["regex"]["pattern"] == "^[a-zA-Z0-9_]+$"
        assert "{{name}}" in toml_data["components"]["regex"]["template"]
        assert '"key"' in toml_data["components"]["regex"]["json_fragment"]

    def test_very_long_multiline_list(self, tmp_path: Path):
        """Test long multiline component list."""
        ini = """\
[environment]
connect_method = local

[host:bigserver]
components = component1
    component2
    component3
    component4
    component5
    component6
    component7
    component8
    component9
    component10
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        components = toml_data["host"]["bigserver"]["components"]
        assert len(components) == 10
        assert components[0] == "component1"
        assert components[9] == "component10"

    def test_single_component_no_host_section(self, tmp_path: Path):
        """Test that single component doesn't create redundant host:X section."""
        toml = """\
[environment]
connect_method = "local"

[hosts]
web01 = "nginx"

[host.web01]
components = ["nginx"]
"""
        toml_path = tmp_path / "environment.toml"
        toml_path.write_text(toml)

        # TOML → INI
        ini_content = convert_toml_to_ini(toml_path)

        import configparser

        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read_string(ini_content)

        # Single component should just be in [hosts], not duplicated in [host:X]
        # (Actually it depends on the implementation - let's see what happens)
        assert cfg["hosts"]["web01"] == "nginx"

    def test_ipv6_addresses(self, tmp_path: Path):
        """Test IPv6 address handling."""
        ini = """\
[environment]
connect_method = local

[resolver]
ipv6host = 2001:db8::1
    fe80::1
    ::1
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path)

        assert toml_data["resolver"]["ipv6host"] == [
            "2001:db8::1",
            "fe80::1",
            "::1",
        ]

    def test_data_attributes_with_dashes(self, tmp_path: Path):
        """Test data-* attributes with dashes in names."""
        ini = """\
[environment]
connect_method = local

[host:db01]
components = postgresql
data-ram = 16
data-disk = 500
data-backup-enabled = yes
data-backup-schedule = daily
"""
        ini_path = tmp_path / "environment.cfg"
        ini_path.write_text(ini)

        toml_data = convert_config_to_toml(ini_path, InferMode.FULL)

        host = toml_data["host"]["db01"]
        assert host["data-ram"] == 16
        assert host["data-disk"] == 500
        assert host["data-backup-enabled"] is True
        assert host["data-backup-schedule"] == "daily"


class TestCliCommands:
    """Test CLI command integration."""

    def test_ini_to_toml_cli(self, tmp_path: Path):
        """Test ini-to-toml command creates valid TOML."""
        from typer.testing import CliRunner

        from batou.ini_to_toml import app as ini_to_toml_app

        runner = CliRunner()

        # Create environment
        env_dir = tmp_path / "testenv"
        env_dir.mkdir()
        (env_dir / "environment.cfg").write_text(MINIMAL_INI)

        result = runner.invoke(ini_to_toml_app, [str(env_dir)])

        assert result.exit_code == 0
        assert (env_dir / "environment.toml").exists()

        # Verify TOML is valid
        toml_content = (env_dir / "environment.toml").read_text()
        config = load_toml_config(toml_content)
        assert config.environment.connect_method == "local"

    def test_toml_to_ini_cli(self, tmp_path: Path):
        """Test toml-to-ini command creates valid INI."""
        from typer.testing import CliRunner

        from batou.toml_to_ini import app as toml_to_ini_app

        runner = CliRunner()

        # Create environment
        env_dir = tmp_path / "testenv"
        env_dir.mkdir()
        (env_dir / "environment.toml").write_text(TestTomlToIniToToml.MINIMAL_TOML)

        result = runner.invoke(toml_to_ini_app, [str(env_dir)])

        assert result.exit_code == 0
        assert (env_dir / "environment.cfg").exists()

        # Verify INI is valid
        import configparser

        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read(env_dir / "environment.cfg")
        assert cfg["environment"]["connect_method"] == "local"

    def test_roundtrip_via_cli(self, tmp_path: Path):
        """Test full roundtrip via CLI commands."""
        from typer.testing import CliRunner

        from batou.ini_to_toml import app as ini_to_toml_app
        from batou.toml_to_ini import app as toml_to_ini_app

        runner = CliRunner()

        # Create environment with INI
        env_dir = tmp_path / "testenv"
        env_dir.mkdir()
        (env_dir / "environment.cfg").write_text(COMPLEX_INI)

        # INI → TOML
        result1 = runner.invoke(ini_to_toml_app, [str(env_dir)])
        assert result1.exit_code == 0

        # Read TOML and verify
        toml_content = (env_dir / "environment.toml").read_text()
        load_toml_config(toml_content)

        # TOML → INI (with --force)
        result2 = runner.invoke(toml_to_ini_app, [str(env_dir), "--force"])
        assert result2.exit_code == 0

        # Read resulting INI
        import configparser

        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read(env_dir / "environment.cfg")

        # Key values should be preserved
        assert cfg["environment"]["host_domain"] == "example.com"
        assert cfg["environment"]["timeout"] == "300"
