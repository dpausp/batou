{
  buildPythonPackage,
  requests,
  pyyaml,
  execnet,
  importlib-metadata,
  importlib-resources,
  remote-pdb,
  py,
  configupdater,
  setuptools,
  jinja2,
  pydantic,
  pydantic-settings,
  rich,
  src,
  # Optional: pyrage extra (age encryption support)
  # Remove bcrypt, cryptography, and pyrage from propagatedBuildInputs
  # if you don't need age encryption
  bcrypt,
  cryptography,
  rustPlatform,
  fetchFromGitHub,
  cargo,
  rustc,
  setuptools-rust,
}:
let
  # pyrage is an optional dependency for age encryption
  # Comment out this block and remove from propagatedBuildInputs if not needed
  pyrage = buildPythonPackage rec {
    pname = "pyrage";
    version = "1.3.0";

    src = fetchFromGitHub {
      owner = "woodruffw";
      repo = pname;
      rev = "v${version}";
      # Update hash with: nix-prefetch fetchFromGitHub --owner woodruffw --repo pyrage --rev v1.3.0
      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };

    cargoDeps = rustPlatform.fetchCargoTarball {
      inherit src;
      name = "${pname}-${version}";
      # Update hash after first build attempt (will show correct hash in error)
      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };

    format = "pyproject";

    nativeBuildInputs = [
      cargo
      rustPlatform.cargoSetupHook
      rustPlatform.maturinBuildHook
      rustc
      setuptools-rust
    ];
  };
in
buildPythonPackage {
  pname = "batou";
  version = "latest";
  inherit src;

  propagatedBuildInputs = [
    configupdater
    jinja2
    pydantic
    pydantic-settings
    requests
    setuptools
    execnet
    importlib-metadata
    importlib-resources
    py
    pyyaml
    rich
    remote-pdb
    # Optional pyrage extra
    bcrypt
    cryptography
    pyrage
  ];
}
