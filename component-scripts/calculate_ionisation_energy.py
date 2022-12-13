#! /usr/bin/env python

# Copyright IBM Inc. 2015, 2019. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Author(s):
#   Michael Johnston

import pandas


if __name__ == "__main__":

    import optparse

    usage = "usage: %prog [options] [base molecule results] [oxidised molecule results]"

    parser = optparse.OptionParser(usage=usage, version="% 0.1", description=__doc__)

    parser.add_option("--logLevel", dest="logLevel",
                      help="The level of logging. Default %default",
                      type="int",
                      default=30,
                      metavar="LOGGING")
    parser.add_option("-t", "--type", dest="type",
                        help="The type of the ionisation potential. Depends on how the oxidised molecule calculation was performed",
                        type="choice",
                        choices=["adiabatic", "vertical"],
                        default="adiabatic")
    parser.add_option("-o", "--output", dest="output",
                    help="The output filename",
                      default='ionisation_energy.csv',
                      metavar="OUTPUT")

    options, args = parser.parse_args()

    baseResults: pandas.DataFrame = pandas.read_csv(args[0], engine="python", sep=None)
    oxidisedResults: pandas.DataFrame = pandas.read_csv(args[1], engine="python", sep=None)

    results = pandas.DataFrame()

    from_base_translate = {'homo': 'koopmans'}

    for x in ['label', 'homo']:
        results[from_base_translate.get(x, x)] = baseResults[x]

    for x in ['excitation-energy', 'osc-str-max']:
        results[x] = oxidisedResults[x]

    print("Joined results are")
    print(results)

    results.to_csv(options.output, index=False, sep=',')
