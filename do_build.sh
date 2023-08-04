#!/bin/bash

set -euo pipefail


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -rf /tmp/kolla-tmpdir
mkdir /tmp/kolla-tmpdir

KOLLA_LOCAL_CHECKOUT=../kolla ./run.sh \
    kolla-build \
        --config-file kolla-build.conf \
        --template-override kolla-template-overrides.j2 \
        --work-dir /tmp/kolla-tmpdir \
        --profile neutron \
        --profile blazar
