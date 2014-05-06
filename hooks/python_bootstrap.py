# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import optparse

import cPickle as pickle


def main():
    # parse command line arguments
    opts = parse_args()

    # load the utilities module
    utilities = None
    try:
        sys.path.append(os.path.dirname(opts.utilities))
        (module_name, _) = os.path.splitext(os.path.basename((opts.utilities)))
        utilities = __import__(module_name)

        # load up the pickle file with the data payload
        data = pickle.load(open(opts.data, "rb"))

        # launch the engine
        engine = utilities.start_engine(data)
        utilities.start_app(engine)
    except Exception:
        if utilities is not None:
            # send the error back to the GUI proxy
            utilities.handle_error(data)
        raise


def parse_args():
    # parse and verify args
    parser = optparse.OptionParser()
    parser.add_option('-d', '--data', help='pickle file with startup data')
    parser.add_option('-u', '--utilities',
        help='path to the python module that defines startup utilities')
    (opts, args) = parser.parse_args()

    if opts.data is None:
        print "Data not specified"
        parser.print_help()
        return -1

    if not os.path.exists(opts.data):
        print "Data file not found."
        return -1

    if opts.utilities is None:
        print "Utilities not specified"
        parser.print_help()
        return -1

    if not os.path.exists(opts.utilities):
        print "Utilities file not found."
        return -1

    return opts

if __name__ == "__main__":
    result = main()
    sys.exit(result)
