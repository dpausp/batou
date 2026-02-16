"""Tests for TOML + Pydantic configuration loading."""

import pytest

from batou.config_toml import (
    ConfigLoadError,
    DictConfig,
    DictConfigSection,
    EnvironmentConfig,
    HostConfig,
    EnvironmentSettings,
    load_toml_config,
    to_legacy_format,
)


class TestEnvironmentSettings:
    """Tests for [environment] section validation."""

    def test_defaults(self):
        """Test default values."""
        settings = EnvironmentSettings()
        assert settings.connect_method == "ssh"
        assert settings.update_method == "rsync"
        assert settings.timeout == 120
        assert settings.jobs == 1

    def test_valid_connect_method(self):
        """Test all valid connect methods."""
        for method in ["local", "ssh", "vagrant", "kitchen"]:
            settings = EnvironmentSettings(connect_method=method)
            assert settings.connect_method == method

    def test_invalid_connect_method(self):
        """Test invalid connect method raises error."""
        with pytest.raises(Exception) as exc_info:
            EnvironmentSettings(connect_method="invalid")
        assert "connect_method" in str(exc_info.value)

    def test_valid_update_method(self):
        """Test all valid update methods."""
        for method in [
            "rsync",
            "rsync-ext",
            "git-bundle",
            "git-pull",
            "hg-bundle",
            "hg-pull",
        ]:
            settings = EnvironmentSettings(update_method=method)
            assert settings.update_method == method

    def test_invalid_update_method(self):
        """Test invalid update method raises error."""
        with pytest.raises(Exception) as exc_info:
            EnvironmentSettings(update_method="invalid")
        assert "update_method" in str(exc_info.value)

    def test_timeout_validation(self):
        """Test timeout must be positive."""
        with pytest.raises(Exception) as exc_info:
            EnvironmentSettings(timeout=0)
        assert "timeout" in str(exc_info.value)

        with pytest.raises(Exception) as exc_info:
            EnvironmentSettings(timeout=-1)
        assert "timeout" in str(exc_info.value)

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(Exception) as exc_info:
            EnvironmentSettings(unknown_field="value")
        assert "unknown_field" in str(exc_info.value)


class TestHostConfig:
    """Tests for host configuration."""

    def test_empty(self):
        """Test empty host config."""
        host = HostConfig()
        assert host.components == []

    def test_with_components(self):
        """Test host with components list."""
        host = HostConfig(components=["nginx", "mysql"])
        assert host.components == ["nginx", "mysql"]

    def test_data_attributes(self):
        """Test data-* attributes are allowed."""
        host = HostConfig(components=["nginx"], **{"data-ram": 4, "data-disk": 40})
        attrs = host.get_data_attributes()
        assert attrs["data-ram"] == "4"
        assert attrs["data-disk"] == "40"


class TestLoadTomlConfig:
    """Tests for TOML loading and validation."""

    def test_minimal_config(self):
        """Test minimal valid config."""
        toml = """
[environment]
connect_method = "local"
"""
        config = load_toml_config(toml)
        assert config.environment.connect_method == "local"

    def test_simple_hosts(self):
        """Test simple host mapping."""
        toml = """
[hosts]
localhost = "hello"
host2 = "myapp"
"""
        config = load_toml_config(toml)
        assert "localhost" in config.hosts
        assert config.hosts["localhost"].components == ["hello"]

    def test_detailed_host_config(self):
        """Test detailed host config with data attributes."""
        toml = """
[host.web01]
components = ["nginx", "mysql"]
data-ram = 4
data-roles = ["web", "db"]
"""
        config = load_toml_config(toml)
        assert "web01" in config.host
        assert config.host["web01"].components == ["nginx", "mysql"]

    def test_component_overrides(self):
        """Test component overrides."""
        toml = """
[components.myapp]
database_host = "db.example.com"
database_port = 5432
debug = false
"""
        config = load_toml_config(toml)
        assert config.components["myapp"]["database_host"] == "db.example.com"
        assert config.components["myapp"]["database_port"] == 5432
        assert config.components["myapp"]["debug"] is False

    def test_resolver(self):
        """Test DNS resolver overrides."""
        toml = """
[resolver]
"db.internal" = "10.0.1.50"
"""
        config = load_toml_config(toml)
        assert config.resolver["db.internal"] == "10.0.1.50"

    def test_resolver_multiline(self):
        """Test DNS resolver with multiple IPs."""
        toml = """
[resolver]
"multi.internal" = ["10.0.1.50", "10.0.1.51"]
"""
        config = load_toml_config(toml)
        assert config.resolver["multi.internal"] == ["10.0.1.50", "10.0.1.51"]

    def test_invalid_toml_syntax(self):
        """Test invalid TOML syntax error."""
        toml = """
[environment
host = "test"
"""
        with pytest.raises(ConfigLoadError) as exc_info:
            load_toml_config(toml, "test.toml")
        assert "Invalid TOML syntax" in str(exc_info.value)

    def test_type_validation_error(self):
        """Test type validation error."""
        toml = """
[environment]
timeout = "not-a-number"
"""
        with pytest.raises(ConfigLoadError) as exc_info:
            load_toml_config(toml, "test.toml")
        assert "timeout" in str(exc_info.value)
        assert "integer" in str(exc_info.value).lower()

    def test_literal_validation_error(self):
        """Test literal validation error for enums."""
        toml = """
[environment]
connect_method = "invalid-method"
"""
        with pytest.raises(ConfigLoadError) as exc_info:
            load_toml_config(toml, "test.toml")
        assert "connect_method" in str(exc_info.value)

    def test_extra_field_error(self):
        """Test error on unknown fields."""
        toml = """
[environment]
unknown_field = "value"
"""
        with pytest.raises(ConfigLoadError) as exc_info:
            load_toml_config(toml, "test.toml")
        assert "unknown_field" in str(exc_info.value)

    def test_invalid_host_value(self):
        """Test error on invalid host config."""
        toml = """
[hosts]
localhost = 123
"""
        with pytest.raises(ConfigLoadError) as exc_info:
            load_toml_config(toml, "test.toml")
        assert "localhost" in str(exc_info.value)


class TestToLegacyFormat:
    """Tests for legacy format conversion."""

    def test_environment_section(self):
        """Test environment section conversion."""
        toml = """
[environment]
host_domain = "example.com"
timeout = 300
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert "environment" in legacy
        assert legacy["environment"]["host_domain"] == "example.com"
        assert legacy["environment"]["timeout"] == "300"

    def test_hosts_section(self):
        """Test hosts section conversion."""
        toml = """
[hosts]
host1 = "nginx"
host2 = "mysql"
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert "hosts" in legacy
        assert legacy["hosts"]["host1"] == "nginx"
        assert legacy["hosts"]["host2"] == "mysql"

    def test_host_detailed_section(self):
        """Test detailed host section conversion."""
        toml = """
[host.web01]
components = ["nginx", "mysql"]
data-ram = 4
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert "host:web01" in legacy
        assert "nginx\nmysql" in legacy["host:web01"]["components"]
        assert legacy["host:web01"]["data-ram"] == "4"

    def test_component_overrides(self):
        """Test component overrides conversion."""
        toml = """
[components.myapp]
database_host = "db.example.com"
database_port = 5432
debug = true
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert "component:myapp" in legacy
        assert legacy["component:myapp"]["database_host"] == "db.example.com"
        assert legacy["component:myapp"]["database_port"] == "5432"
        assert legacy["component:myapp"]["debug"] == "True"

    def test_list_to_newline_string(self):
        """Test list conversion to newline-separated string."""
        toml = """
[components.myapp]
hosts = ["host1", "host2", "host3"]
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert legacy["component:myapp"]["hosts"] == "host1\nhost2\nhost3"

    def test_resolver_section(self):
        """Test resolver section conversion."""
        toml = """
[resolver]
"db.internal" = "10.0.1.50"
"multi.internal" = ["10.0.2.1", "10.0.2.2"]
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert "resolver" in legacy
        assert legacy["resolver"]["db.internal"] == "10.0.1.50"
        assert legacy["resolver"]["multi.internal"] == "10.0.2.1\n10.0.2.2"


class TestDictConfig:
    """Tests for DictConfig compatibility class."""

    def test_contains(self):
        """Test __contains__ method."""
        config = DictConfig({"section": {"key": "value"}})
        assert "section" in config
        assert "missing" not in config

    def test_getitem(self):
        """Test __getitem__ method."""
        config = DictConfig({"section": {"key": "value"}})
        assert config["section"]["key"] == "value"

    def test_get(self):
        """Test get method."""
        config = DictConfig({"section": {"key": "value"}})
        assert config.get("section") == {"key": "value"}
        assert config.get("missing", {}) == {}

    def test_iter(self):
        """Test __iter__ method."""
        config = DictConfig({"a": {}, "b": {}, "c": {}})
        assert list(config) == ["a", "b", "c"]

    def test_options(self):
        """Test options method."""
        config = DictConfig({"section": {"key1": "v1", "key2": "v2"}})
        assert set(config.options("section")) == {"key1", "key2"}

    def test_as_list_comma(self):
        """Test as_list with comma-separated values."""
        section = DictConfigSection({"key": "a, b, c"})
        assert section.as_list("key") == ["a", "b", "c"]

    def test_as_list_newline(self):
        """Test as_list with newline-separated values."""
        section = DictConfigSection({"key": "a\nb\nc"})
        assert section.as_list("key") == ["a", "b", "c"]

    def test_as_list_single(self):
        """Test as_list with single value."""
        section = DictConfigSection({"key": "single"})
        assert section.as_list("key") == ["single"]


class TestIntegration:
    """Integration tests with real-world configs."""

    def test_complex_production_config(self):
        """Test a complex production-like configuration."""
        toml = """
[environment]
host_domain = "example.com"
platform = "nixos"
service_user = "service_user"
update_method = "git-bundle"
branch = "master"

[hosts]
host01 = "frontend"

[host.host01]
components = [
    "copypreislistetonfs",
    "crontab",
    "frontendrebuild",
    "haproxy",
]
data-description = "Frontend"
data-ram = 4
data-disk = 40
data-cores = 1
data-roles = ["docker", "mailstub", "nfs_rg_client"]

[host.host02]
components = ["crontab", "mysqlserver", "postgresql", "rediscache", "solr"]
data-description = "MySQL, Solr, Redis"
data-ram = 32
data-disk = 1000

[components.provision]
project = "testproject"
vm_environment = "fc-25.11-staging"

[components.settings]
versions_ini = "versions-testing.ini"
app_env = "testproject"
password_protected = true
verlag_ids = ["publisher1", "publisher2"]

[resolver]
"db.internal" = "10.0.1.50"
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        # Verify environment
        assert config.environment.host_domain == "example.com"
        assert config.environment.platform == "nixos"

        # Verify hosts merged correctly
        all_hosts = config.get_all_hosts()
        assert len(all_hosts) == 2
        assert len(all_hosts["host01"].components) == 4
        assert len(all_hosts["host02"].components) == 5

        # Verify legacy format
        assert "hosts" in legacy
        assert "host:host01" in legacy
        assert "host:host02" in legacy
        assert "component:provision" in legacy
        assert "component:settings" in legacy
        assert "resolver" in legacy

    def test_minimal_local_config(self):
        """Test minimal local development config."""
        toml = """
[environment]
connect_method = "local"

[hosts]
localhost = "myapp"
"""
        config = load_toml_config(toml)
        legacy = to_legacy_format(config)

        assert config.environment.connect_method == "local"
        assert "localhost" in legacy["hosts"]
