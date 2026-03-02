#!/bin/sh

set -e

base=$PWD
gpg="gpg --homedir ${base}/src/batou/secrets/tests/fixture/gnupg -e --yes -r 03C7E67FC9FD9364 -r 306151601E813A47"

cd ${base}/src/batou/secrets/tests/fixture
$gpg -o encrypted.cfg.gpg cleartext.cfg

cd ${base}/examples/errors
$gpg -o environments/errors/secrets.cfg.gpg secrets.cfg.clear

cd ${base}/examples/errors2
$gpg -o environments/errors/secrets.cfg.gpg secrets.cfg.clear

cd ${base}/examples/tutorial-secrets
$gpg -o environments/tutorial/secrets.cfg.gpg tutorial-secrets.cfg.clear
$gpg -o environments/tutorial/secret-foobar.yaml.gpg tutorial-foobar.yaml.clear
$gpg -o environments/gocept/secrets.cfg.gpg gocept-secrets.cfg.clear
