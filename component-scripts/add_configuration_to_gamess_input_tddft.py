#! /usr/bin/env python

# Copyright IBM Inc. 2015, 2019, 2020. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Author(s):
#   James McDonagh
#   Michael Johnston
#   Vassilis Vassiliadis

from __future__ import print_function
from __future__ import annotations
import re
import sys
import logging
import os
import glob
from datetime import datetime

__version__ = "0.1"
__title__ = os.path.basename(__file__)
__copyright__ = "Copyright IBM Corp. 2020"


def glob_conditional(path: str):
    '''Performs glob search ONLY if path contains magic characters, else it returns just the input path'''

    if glob.has_magic(path):
        return glob.glob(path)
    else:
        return [path]


def setup_logger(cwd, loglev="INFO"):
    """
    Make logger setup
    INPUT :
        cwd : the working directory you want the log file to be saved in
    OUTPUT:
        FILE: log file
    """
    # set log level from user
    intloglev = getattr(logging, loglev)
    try:
        intloglev + 1
    except TypeError:
        print("ERROR - cannot convert loglev to numeric value using default of 20 = INFO")
        with open("error_logging.log", "w+") as logerr:
            logerr.write("ERROR - cannot convert loglev to numeric value using default of 20 = INFO")
        intloglev = 20

    # Format routine the message comes from, the leve of the information debug, info, warning, error, critical
    # writes all levels to teh log file Optimizer.log
    logging.raiseExceptions = True
    log = logging.getLogger()
    log.setLevel(intloglev)
    pathlog = os.path.join(cwd, "{}.log".format(__title__.split(".")[0]))

    # File logging handle set up
    filelog = logging.FileHandler("{}".format(pathlog), mode="w")
    filelog.setLevel(intloglev)
    fileformat = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
    filelog.setFormatter(fileformat)

    # Setup handle for screen printing only prints info and above not debugging info
    screen = logging.StreamHandler()
    screen.setLevel(10)
    screenformat = logging.Formatter('%(message)s')
    screen.setFormatter(screenformat)

    # get log instance
    log.addHandler(screen)
    log.addHandler(filelog)

    log.info("The handlers {} logging level {} {}".format(log.handlers, loglev, intloglev))
    log.info('Started {}\n'.format(datetime.now()))

    return log



if __name__ == "__main__":

    import optparse

    usage = "usage: %prog [options] [gamess molecule data file] [gamess input file]"

    parser = optparse.OptionParser(usage=usage, version="% 0.1", description=__doc__)

    parser.add_option("--logLevel", dest="logLevel",
                      help="The level of logging. Default %default",
                      type="int",
                      default=30,
                      metavar="LOGGING")
    parser.add_option("-i", "--iteration", dest="iteration",
                    help="The iteration to get the configuration from",
                    type=int,
                      default=0,
                      metavar="ITERATION")
    parser.add_option("-o", "--output", dest="output",
                    help="The output filename",
                      default='gamess.inp',
                      metavar="OUTPUT")
    parser.add_option("-c", "--checkOptimisation", dest="checkOptimisation",
                    help="Checks the given GAMESS log file to see if the run completed successfully. If not exits with 1",
                      default=None,
                      metavar="CHECK")

    options, args = parser.parse_args()
    start = -1

    # ----------- Check optimization and get charge and spin from it -------------------

    log = setup_logger(os.getcwd())
    
    for inx, a in enumerate(args):
        log.info("\t{} {}\n".format(inx, a))

    if options.checkOptimisation is not None:

        path = glob_conditional(options.checkOptimisation)[0]

        with open(path) as f:
            lines = f.readlines()

        optimisationCompleted = False
        term_norm = False
        spin_found = False
        charge_found = False
        for l in lines:

            log.debug(l)

            if l.find("MULT=") != -1:
                log.debug(l)
                llist = re.split("\W+",l)
                log.debug(llist)
                inx = next(inx for inx, tmp in enumerate(llist) if re.search(r"MULT", tmp))
                log.debug(inx)
                str_mult = llist[inx+1].strip()
                spin_found = True
                log.info("Spin {}".format(str_mult))

            if l.find("ICHARG=") != -1:
                log.debug(l)
                llist = re.split("\W+",l)
                log.debug(llist)
                inx = next(inx for inx, tmp in enumerate(llist) if re.search(r"ICHAR", tmp))
                log.debug(inx)
                str_charge = llist[inx+1].strip()
                charge_found = True
                log.info("Charge {}".format(str_charge))

            if l.find('TERMINATED NORMALLY') != -1 or l.find('gracefully') != -1: 
                term_norm = True
    
            if l.find("EQUILIBRIUM GEOMETRY LOCATED") != -1: 
                optimisationCompleted = True

        if optimisationCompleted is False or term_norm is False :
            print("Optimisation did not execute successfully and check-optimisation is set. Aborting",file=sys.stderr)
            log.error("Optimisation did not execute successfully and check-optimisation is set. Aborting")
            raise RuntimeError
        else:
            print("Optimisation completed successfully - proceeding to extract structure", file=sys.stderr)
            log.info("Optimisation completed successfully - proceeding to extract structure")

        if charge_found is False:
            log.warning("Setting charge to default 0, as it was not found in the geometry optimization output")
            str_charge = 0

        if spin_found is False:
            log.warning("Setting spin to default 1, as it was not found in the geometry optimization output")
            str_mult = 1

    else:
        log.warning("Setting charge to default 0, because no geometry optimization output to check")
        str_charge = 0

        log.warning("Setting spin to default 1, because no geometry optimization output to check")
        str_mult = 1

    # ----------- Get geometry from last optimzation run -------------------

    with open(args[0]) as f:
        lines = f.readlines()

    if options.iteration == -1:
        lines.reverse()    
        restr = "DATA FROM NSERCH"     
        regex = re.compile(restr)

        for i,line in enumerate(lines):
            if regex.search(line):
                start = i
                break

        if start == -1:
            print('Cannot not find any optimised geometry', file=sys.stderr)
            log.error('Cannot not find any optimised geometry')
            raise RuntimeError

        lines = lines[:start-4+1]
        lines.reverse()
    else:
        restr = "DATA FROM NSERCH=[\s]+%d" % options.iteration    
        regex = re.compile(restr)

        for i,line in enumerate(lines):
            if regex.search(line):
                start = i
                break

        if start == -1:
            print('Cannot not find optimised geometry for iteration {}'.format(options.iteration), file=sys.stderr)
            log.error('Cannot not find optimised geometry for iteration {}'.format(options.iteration))
            raise RuntimeError

        lines = lines[start+4:]

    regex = re.compile('^---')
    end = len(lines)
    for i,line in enumerate(lines):
        if regex.search(line):
            end = i
            break

    conf = lines[:end]
    for l in conf:
        log.info("{}".format(l))

    # ----------- Write new input -------------------

    lines = []
    log.info("opening {}".format(args[1]))
    with open(args[1]) as f:
        for line in f:

            # NOTE: the split of the line is on white space and assumes no 
            # space between = signs eg abc=xzy 
            if "$DATA" in line:
                break

            if "MULT" in line:
                log.debug(line)
                l = re.split("[\s]",line)
                log.debug(l)
                inx = next(inx for inx, tmp in enumerate(l) if re.search(r"MULT", tmp))
                log.debug(inx)
                line = " ".join(l[:inx] + ["MULT={}".format(str_mult)] + l[inx+1:] + ["\n"])
                log.debug(line)
                log.info("Set mult to {}".format(str_mult))

            if "ICHARG" in line:
                log.debug(line)
                l = re.split("[\s]",line)
                log.debug(l)
                inx = next(inx for inx, tmp in enumerate(l) if re.search(r"ICHARG", tmp))
                log.debug(inx)
                line = " ".join(l[:inx] + ["ICHARG={}".format(str_charge)] + l[inx+1:] + ["\n"])
                log.debug(line)
                log.info("Set icharg to {}".format(str_charge))
            
            if "SCFTYP" in line and str_mult != "1":
                log.debug(line)
                l = re.split("[\s]",line)
                log.debug(l)
                inx = next(inx for inx, tmp in enumerate(l) if re.search(r"SCFTYP", tmp))
                line = " ".join(l[:inx] + ["SCFTYP=UHF"] + l[inx+1:] + ["\n"])
                log.debug(line)
                log.info("Set scftyp to rohf as spin is not 1 hence is an openshell system")
            
            lines.append(line)

    lines.append(' $DATA\n')     
    lines.append('\n')     
    lines.append('C1\n')
    lines.extend(conf)
    lines.append(' $END\n')

    with open(options.output, 'w') as f:
       f.writelines(lines)
    
    log.info("written to {}".format(options.output))
