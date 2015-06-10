# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
import shutil
import optparse


def main():
    opts = parse_args()

    # import toolkit from the specified core install
    sys.path.insert(0, opts.core_python_path)
    import sgtk
    if hasattr(sgtk, "set_authenticated_user"):
        # import authentication
        from tank_vendor import shotgun_authentication
        # Initialize the authenticator with Toolkit's defaults manager.
        dm = sgtk.util.CoreDefaultsManager()
        sg_auth = shotgun_authentication.ShotgunAuthenticator(dm)
        # get the current user
        user = sg_auth.get_default_user()
        sgtk.set_authenticated_user(user)

    import sgtk.platform.engine

    # load up toolkit and get the environment for the project context
    tk = sgtk.sgtk_from_path(opts.configuration_path)
    ctx = tk.context_from_entity("Project", int(opts.project_id))
    env = sgtk.platform.engine.get_environment_from_context(tk, ctx)

    # make a backup of the original yml file
    shutil.copy(env.disk_location, "%s.orig" % env.disk_location)

    # install the tk-desktop engine if it is not installed
    if "tk-desktop" not in env.get_engines():
        install_cmd = tk.get_command("install_engine")
        params = {
            "environment": env.name,
            "engine_uri": "tk-desktop",
        }
        install_cmd.execute(params)

        # reload the new environment
        env = sgtk.platform.engine.get_environment_from_context(tk, ctx)

    # copy the apps from tk-shell
    copy_apps_cmd = tk.get_command("copy_apps")
    params = {
        "environment": env.name,
        "src_engine_instance": "tk-shell",
        "dst_engine_instance": "tk-desktop",
    }
    copy_apps_cmd.execute(params)


def parse_args():
    # parse and verify args
    parser = optparse.OptionParser()
    parser.add_option("--core_python_path", help="path to the python directory of the core install to use")
    parser.add_option("--configuration_path", help="path to the configuration to modify")
    parser.add_option("--project_id", help="id of the project we are modifying the config of")

    (opts, args) = parser.parse_args()

    if opts.core_python_path is None:
        raise ValueError("required parameter 'core_python_path' not set")
    if opts.configuration_path is None:
        raise ValueError("required parameter 'configuration_path' not set")
    if opts.project_id is None:
        raise ValueError("required parameter 'project_id' not set")

    return opts

if __name__ == "__main__":
    try:
        result = main()
    except Exception, e:
        sys.stderr.write("%s" % e)
        sys.exit(-1)

    # success
    sys.exit(0)
