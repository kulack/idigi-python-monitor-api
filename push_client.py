# ***************************************************************************
# Copyright (c) 2012 Digi International Inc.,
# All rights not expressly granted are reserved.
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
# 
# Digi International Inc. 11001 Bren Road East, Minnetonka, MN 55343
#
# ***************************************************************************
"""
Push Client Example

An example push_client method.  Call with '-h' for usage.

Demonstrates simple xml and json callbacks for printing data as it is 
received.
"""
import getpass

import argparse
import json
import logging
import time

from xml.dom.minidom import parseString
from idigi_monitor_api import push_client

LOG = logging.getLogger("push_client")

def json_cb(data):
    """
    Sample callback, parses data as json and pretty prints it.
    Returns True if json is valid, False otherwise.

    :param data: The payload of the PublishMessage.
    """
    try:
        json_data = json.loads(data)
        LOG.info("Data Received %s" % json.dumps(json_data, sort_keys=True, 
                    indent=4))
        return True
    except Exception as exception:
        print(exception)

    return False

def xml_cb(data):
    """
    Sample callback, parses data as xml and pretty prints it.
    Returns True if xml is valid, False otherwise.
    
    :param data: The payload of the PublishMessage.
    """
    try:
        dom = parseString(data)
        LOG.info("Data Received: %s" % (dom.toprettyxml()))
        return True
    except Exception as exception:
        print(exception)
    
    return False

def get_parser():
    """ Parser for this script """
    parser = argparse.ArgumentParser(description="iDigi Push Client Sample", 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('username', type=str,
        help='Username to authenticate with.')

    parser.add_argument('password', type=str, nargs='?', default=None,
        help='Password to authenticate with.')

    parser.add_argument('--topics', '-t', dest='topics', action='store', 
        type=str, default='DeviceCore', 
        help='A comma-separated list of topics to listen on.')

    parser.add_argument('--host', '-a', dest='host', action='store', 
        type=str, default='my.idigi.com', 
        help='iDigi server to connect to.')

    parser.add_argument('--insecure', dest='insecure', action='store_true',
        default=False,
        help='Prevent client from making secure (SSL) connection.')

    parser.add_argument("--nonprod", dest="nonprod", action="store_true",
                        default=False,
                        help="Do not use public production certificates, "
                             "but still use a secure connection")

    parser.add_argument('--compression', '-c',  dest='compression', 
        action='store', type=str, default='gzip', choices=['none', 'gzip'],
        help='Compression type to use.')

    parser.add_argument('--format', '-f', dest='format', action='store',
        type=str, default='json', choices=['json', 'xml'],
        help='Format data should be pushed up in.')

    parser.add_argument('--batchsize', '-b', dest='batchsize', action='store',
        type=int, default=1,
        help='Amount of messages to batch up before sending data.')

    parser.add_argument('--batchduration', '-d', dest='batchduration', 
        action='store', type=int, default=60,
        help='Seconds to wait before sending batch if batchsize not met.')
    
    return parser

def main():
    """ Main function call """
    args = get_parser().parse_args()
    if args.password is None:
        args.password = getpass.getpass(f"Password for user {args.username} at {args.host}:")

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', 
                datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
    LOG.info("Creating Push Client.")

    ca_certs = None
    if args.nonprod:
        ca_certs="nonprod"
    client = push_client(args.username, args.password, hostname=args.host,
                        secure=not args.insecure, ca_certs=ca_certs)

    topics = args.topics.split(',')

    LOG.info("Checking to see if Monitor Already Exists.")
    monitor_id = client.get_monitor(topics)

    # Delete Monitor if it Exists.
    if monitor_id is not None:
        LOG.info("Monitor already exists, using it.")
        # client.delete_monitor(monitor_id)
    else:
        monitor_id = client.create_monitor(topics, format_type=args.format,
            compression=args.compression, batch_size=args.batchsize,
            batch_duration=args.batchduration)

    try:
        callback = json_cb if args.format == "json" else xml_cb
        client.create_session(callback, monitor_id)
        while True:
            time.sleep(.31416)
    except KeyboardInterrupt:
        # Expect KeyboardInterrupt (CTRL+C or CTRL+D) and print friendly msg.
        LOG.warn("Closing Sessions and Cleaning Up.")
    finally:
        client.stop_all()
        ## LOG.info("Deleting Monitor %s." % monitor_id)
        ## client.delete_monitor(monitor_id)
        LOG.info("Done")

if __name__ == "__main__":
    main()