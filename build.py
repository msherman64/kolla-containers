#!/usr/bin/env python
# Copyright 2021 University of Chicago
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import pathlib
import shutil
import sys

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape
from kolla.image import build as kolla_build
import yaml


@click.command("build")
@click.option("--config-file", default="build_config.yaml")
@click.option("--config-set")
@click.option("--push/--no-push", default=False)
@click.option("--use-cache/--no-use-cache", default=True)
def cli(config_file=None, config_set=None, push=None, use_cache=None):
    build_config = {}
    with open(config_file, "r") as f:
        build_config = yaml.safe_load(f)

    build_dir = pathlib.Path("./build")
    build_dir.mkdir(exist_ok=True)

    kolla_config = {
        "work_dir": str(build_dir),
        "config_file": "kolla-build.conf",
        "template_override": "kolla-template-overrides.j2",
    }

    docker_tag = os.getenv("DOCKER_TAG")
    if docker_tag:
        kolla_config["tag"] = docker_tag
    openstack_release = os.getenv("OPENSTACK_BASE_RELEASE")
    if openstack_release:
        kolla_config["openstack_release"] = openstack_release
    profile = os.getenv("KOLLA_BUILD_PROFILE")
    if profile:
        kolla_config["profile"] = profile

    default_config_set = build_config.get("defaults", {})
    if default_config_set:
        kolla_config.update(default_config_set)

    if config_set:
        config_set = build_config.get("config_sets", {}).get(config_set)
        if not config_set:
            raise ValueError(f"No config set found for '{config_set}'")
        kolla_config.update(config_set)

    kolla_argv = []
    for arg, value in kolla_config.items():
        if value is not None:
            kolla_argv.append(f"--{arg.replace('_', '-')}={value}")

    if push:
        kolla_argv.append("--push")
    if use_cache:
        # Always skip ancestors; we want to explicitly build the ancestor
        # images instead of automagically doing this.
        kolla_argv.append("--skip-parents")
        kolla_argv.append("--cache")

    """
    build_dir="$DIR/build"
    source_dir="$DIR/sources"
    profile_dir="$DIR/$KOLLA_BUILD_PROFILE"
    sub_profile="${KOLLA_BUILD_SUBPROFILE:-$KOLLA_BUILD_PROFILE}"

    # Create build directory with configuration specific to service
    mkdir -p "$build_dir"
    declare -a conf_files=(
        <(sed "s/OPENSTACK_BASE_RELEASE/$OPENSTACK_BASE_RELEASE/" "$DIR/kolla-build.conf.m4")
        "$profile_dir/kolla-build.conf"
    )
    if [[ "$KOLLA_LOCAL_SOURCES" == "yes" && -f "$profile_dir/kolla-build.local-sources.conf" ]]; then
        conf_files+=("$profile_dir/kolla-build.local-sources.conf")
    fi
    cat "${conf_files[@]}" 2>/dev/null >"$build_dir/kolla-build.conf"
    cat "$DIR/kolla-template-overrides.j2" "$profile_dir/kolla-template-overrides.j2" \
        2>/dev/null >"$build_dir/kolla-template-overrides.j2"
    if [[ -d "$profile_dir/additions" ]]; then
    mkdir -p "$source_dir"
        tar -cf "$source_dir/additions.tar" -C "$profile_dir/additions" .
    fi
    """

    # Copy files
    shutil.copy(
        "./kolla-template-overrides.j2",
        build_dir.joinpath("kolla-template-overrides.j2")
    )

    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape()
    )
    kolla_build_conf_tmpl = env.get_template("kolla-build.conf.j2")
    with open(pathlib.Path(build_dir, "kolla-build.conf"), "w") as f:
        f.write(kolla_build_conf_tmpl.render(**kolla_config))

    print("kolla-build \\")
    print("  " + " \\\n  ".join(kolla_argv))
    print()

    # Kolla reads its input straight from sys.argv
    sys.argv = [""] + kolla_argv
    bad, good, unmatched, skipped = kolla_build.run_build()
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    cli()
