import ast
import os
import subprocess
import sys

import execnet.gateway_io
import yaml

import batou.utils
from batou import output, remote_core
from batou.debug.settings import get_debug_settings
from batou.utils import BagOfAttributes

# Keys in os.environ which get propagated to the remote side:
REMOTE_OS_ENV_KEYS = (
    "REMOTE_PDB_HOST",
    "REMOTE_PDB_PORT",
)


# Monkeypatch execnet to support 'vagrant ssh' and 'kitchen exec'.
# 'vagrant' support has been added to 'execnet' release 1.4.
def get_kitchen_ssh_connection_info(name):
    cmd = "kitchen", "diagnose", "--log-level=error", name
    info = yaml.load(subprocess.check_output(cmd))
    (instance,) = list(info["instances"].values())
    state = instance["state_file"]
    return [
        "-o",
        "StrictHostKeyChecking=no",
        "-i",
        state["ssh_key"],
        "-p",
        state["port"],
        "-l",
        state["username"],
        state["hostname"],
    ]


def new_ssh_args(spec):
    from execnet.gateway_io import popen_bootstrapline

    remotepython = spec.python or "python"
    if spec.type == "vagrant":
        args = ["vagrant", "ssh", spec.ssh, "--", "-C"]
    elif spec.type == "kitchen":
        # TODO: this should really use:
        #   args = ['kitchen', 'exec', spec.ssh, '-c']
        # but `exec` apparently doesn't connect stdin (yet)...
        args = ["ssh", "-C"] + get_kitchen_ssh_connection_info(spec.ssh)
    else:
        args = ["ssh", "-C"]
    if spec.ssh_config is not None:
        args.extend(["-F", str(spec.ssh_config)])
    remotecmd = f'{remotepython} -c "{popen_bootstrapline}"'
    if spec.type == "vagrant" or spec.type == "kitchen":
        args.extend([remotecmd])
    else:
        args.extend([spec.ssh, remotecmd])
    return args


execnet.gateway_io.ssh_args = new_ssh_args


class RPCWrapper:
    def __init__(self, host):
        self.host = host

    def __getattr__(self, name):
        def call(*args, **kw):
            output.annotate(
                f"rpc {self.host.fqdn}: {name}(*{args}, **{kw})",
                debug=True,
            )
            self.host.channel.send((name, args, kw))
            while True:
                message = self.host.channel.receive()
                output.annotate(
                    f"{self.host.fqdn}: message: {message}",
                    debug=True,
                )
                type = message[0]
                if type == "batou-result":
                    return message[1]
                elif type == "batou-output":
                    _, output_cmd, args, kw = message
                    getattr(output, output_cmd)(*args, **kw)
                elif type == "batou-unknown-error":
                    output.error(message[1])
                    raise RuntimeError(
                        f"{self.host.fqdn}: Remote exception encountered."
                    )
                elif type == "batou-error":
                    # Remote put out the details already.
                    raise RuntimeError(
                        f"{self.host.fqdn}: Remote exception encountered."
                    )
                else:
                    raise RuntimeError(f"{self.host.fqdn}: Unknown message type {type}")

        return call


_no_value_marker = object()


class Host:
    service_user = None
    require_sudo = None
    ignore = False
    platform = None
    _provisioner = None
    _provision_info: dict
    remap = False
    ignore = False

    def __init__(self, name, environment, config=None):
        # The _name attribute is the name that is given to this host in the
        # environment. The `name` property will return the true name for this
        # host in case that a mapping exists, e.g. due to a provisioner.
        if config is None:
            config = {}
        self._name = name

        self.aliases = BagOfAttributes()

        self.data = {}

        self.rpc = RPCWrapper(self)
        self.environment = environment

        self.ignore = ast.literal_eval(config.get("ignore", "False"))

        self.platform = config.get("platform", environment.platform)
        self.service_user = config.get("service_user", environment.service_user)
        if "require_sudo" in config:
            self.require_sudo = ast.literal_eval(config.get("require_sudo"))
        else:
            self.require_sudo = environment.require_sudo

        self.remap = ast.literal_eval(config.get("provision-dynamic-hostname", "False"))
        self._provisioner = config.get("provisioner")
        self._provision_info = {}
        if self.provisioner:
            self.provisioner.configure_host(self, config)

        for key, value in list(config.items()):
            if key.startswith("data-"):
                key = key.replace("data-", "", 1)
                self.data[key] = value

    @property
    def provisioner(self):
        if self._provisioner == "none":
            # Provisioning explicitly disabled for this host
            return
        elif not self._provisioner:
            # Default provisionier (if available)
            return self.environment.provisioners.get("default")
        return self.environment.provisioners[self._provisioner]

    # These are internal aliases to allow having an explicit name
    # for a host in the environment and then having a provisioner assign a
    # different "true" name for this host.
    @property
    def _aliases(self):
        if self._name == self.name:
            return []
        return [self._name]

    @property
    def name(self):
        mapping = self.environment.hostname_mapping
        if not self.remap:
            # Update the map in case it contained an old persisted entry.
            mapping[self._name] = self._name
        elif self._name not in mapping:
            mapping[self._name] = self.provisioner.suggest_name(self._name)
        return mapping[self._name]

    @property
    def fqdn(self):
        name = self.name
        if self.environment.host_domain:
            name += "." + self.environment.host_domain
        return name

    def deploy_component(self, component, predict_only):
        self.rpc.deploy(component, predict_only)

    def root_dependencies(self):
        return self.rpc.root_dependencies()

    @property
    def components(self):
        return self.environment.components_for(self)

    def summarize(self):
        if self.provisioner:
            self.provisioner.summarize(self)


class LocalHost(Host):
    def connect(self):
        self.gateway = execnet.makegateway(f"popen//python={sys.executable}")
        self.channel = self.gateway.remote_exec(remote_core)

    def start(self):
        self.rpc.lock()

        # Since we reconnected, any state on the remote side has been lost,
        # so we need to set the target directory again (which we only can
        # know about locally).
        self.rpc.setup_output(output.enable_debug)

        env = self.environment

        self.remote_repository = self.rpc.ensure_repository(
            env.target_directory, "local"
        )

        self.remote_base = self.rpc.ensure_base(env.deployment_base)

        # XXX the cwd isn't right.
        return self.rpc.setup_deployment(
            env.name,
            self.name,
            env.overrides,
            batou.utils.resolve_override,
            batou.utils.resolve_v6_override,
            env.secret_files,
            env.secret_data,
            env._host_data(),
            env.timeout,
            env.platform,
            get_debug_settings().model_dump(mode="json"),
        )

    def disconnect(self):
        if hasattr(self, "gateway"):
            self.gateway.exit()


class RemoteHost(Host):
    gateway = None

    def _makegateway(self, interpreter):
        if self.service_user is not None and self.require_sudo:
            # When calling sudo, ensure that no password will ever be
            # requested, and fail otherwise.
            interpreter = f"sudo -ni -u {self.service_user} {interpreter}"
        spec = f"ssh={self.fqdn}//python={interpreter}//type={self.environment.connect_method}"
        ssh_configs = [
            f"ssh_config_{self.environment.name}",
            "ssh_config",
        ]
        for ssh_config in ssh_configs:
            if os.path.exists(ssh_config):
                spec += f"//ssh_config={ssh_config}"
                break

        return execnet.makegateway(spec)

    def connect(self, interpreter="python3"):
        if self.gateway:
            output.annotate("Disconnecting ...", debug=True)
            self.disconnect()

        output.annotate("Connecting ...", debug=True)

        self.gateway = self._makegateway(interpreter)

        try:
            self.channel = self.gateway.remote_exec(remote_core)
        except OSError:
            raise RuntimeError(
                f"Could not start batou on host `{self.fqdn}`. "
                "The output above may contain more information. "
            )

        if self.service_user is not None and self.require_sudo is None:
            # Discover whether we need to invoke sudo to reach the
            # right user.
            remote_user = self.rpc.whoami()
            self.require_sudo = remote_user != self.service_user

            if self.require_sudo:
                output.annotate(
                    "Service user requires sudo, reconnecting ...", debug=True
                )

                self.gateway.exit()
                self.gateway = self._makegateway(interpreter)

                try:
                    self.channel = self.gateway.remote_exec(remote_core)
                except OSError:
                    raise RuntimeError(
                        f"Could not start batou on host `{self.fqdn}`. "
                        "The output above may contain more information. "
                    )

        output.annotate("Connected ...", debug=True)

    def start(self):
        output.step(self.name, "Bootstrapping ...", debug=True)
        self.rpc.lock()
        env = self.environment

        self.remote_repository = self.rpc.ensure_repository(
            env.target_directory, env.update_method
        )
        self.remote_base = self.rpc.ensure_base(env.deployment_base)

        output.step(self.name, "Updating repository ...", debug=True)
        env.repository.update(self)

        self.rpc.build_batou()

        # Now, replace the basic interpreter connection, with a "real" one
        # that has all our dependencies installed.
        #
        # XXX this requires an interesting move of detecting which appenv
        # version we have available to make this backwards compatible.
        self.connect(self.remote_base + "/appenv python")

        # Reinit after reconnect ...
        self.rpc.lock()
        self.remote_repository = self.rpc.ensure_repository(
            env.target_directory, env.update_method
        )
        self.remote_base = self.rpc.ensure_base(env.deployment_base)

        # Since we reconnected, any state on the remote side has been lost,
        # so we need to set the target directory again (which we only can
        # know about locally)
        self.rpc.setup_output(output.enable_debug)

        return self.rpc.setup_deployment(
            env.name,
            self.name,
            env.overrides,
            batou.utils.resolve_override,
            batou.utils.resolve_v6_override,
            env.secret_files,
            env.secret_data,
            env._host_data(),
            env.timeout,
            env.platform,
            get_debug_settings().model_dump(mode="json"),
            {
                key: os.environ.get(key)
                for key in REMOTE_OS_ENV_KEYS
                if os.environ.get(key)
            },
        )

    def disconnect(self):
        if self.gateway is not None:
            self.gateway.exit()
