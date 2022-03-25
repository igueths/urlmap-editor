#!/usr/bin/env python3
#
# Copyright 2022, Igor Gueths
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import sys
import argparse
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap as OrderedDict
# Add command-line arguments.
parser = argparse.ArgumentParser(
    epilog='An URL map editor for manipulating host rules and path matchers. All denoted parameters i.e., hostrule parameters take key=value pairs. All supplementary parameters denoted as valid for various options i.e., defaultService for --pathmatcher, are required.')
parser.add_argument('--pathmatcher', help='path matcher parameters (name/defaultService)',
                    required=True, nargs='+', action='append')
parser.add_argument('--pathrules', help='path rule parameters (path/service)',
                    nargs='+', required=True, action='append')
parser.add_argument('--hostrule', help='host rule parameters (hosts/pathMatcher)',
                    nargs='+', required=True, action='append')
parser.add_argument(
    '--file', help='The filename of the URL map to use', required=True)
args = parser.parse_args()
# Give the arguments their own variables.
pathmatcher = args.pathmatcher
pathrules = args.pathrules
hostrule = args.hostrule
file = args.file
# Methods for manipulating the URL map payload.


def build_pathmatcher(name, defaultServiceUrl):
    """
    This builds and returns a full pathMatcher entry, for appending to an existing URL map.
    Parameters:
    name: The name of the pathMatcher.
    defaultServiceUrl: Denotes the URL requests should go to if none of the path patterns match.
    """
    matcher = OrderedDict()
    matcher['defaultService'] = defaultServiceUrl
    matcher['name'] = name
    return matcher


def build_pathrule(path, serviceUrl):
    """
    This method builds and returns a host rule ordered dict, suitable for appending to a pathMatcher object.
    Parameters:
    path: The absolute or wildcard path to match against (currently only a single path is supported).
    serviceUrl: The service i.e., backend bucket where requests that match the path should be sent.
    """
    rule = OrderedDict()
    rule['paths'] = [path]
    rule['routeAction'] = OrderedDict()
    rule['routeAction']['urlRewrite'] = OrderedDict()
    rule['routeAction']['urlRewrite']['pathPrefixRewrite'] = '/'
    rule['service'] = serviceUrl
    return rule


def build_hostrule(host, pathMatcher):
    """
    This method builds and returns a host rule/pathMatcher ordered dict, for appending to a URL map host list.
    Parameters:
    host: The FQDN to associate with a pathMatcher.
    pathMatcher: The name of the pathMatcher that will be associated with this FQDN.
"""
    rule = OrderedDict()
    rule['hosts'] = [host]
    rule['pathMatcher'] = pathMatcher
    return rule


# Build our dicts and such for passing into the build_XXX methods, starting
# with the host rule.
hostRuleDict = dict()
for l in hostrule:
    # l is a list element.
    for s in l:
        # s is a string we can split on.
        k, v = s.split('=')
        hostRuleDict[k] = v
pathMatcherDict = dict()
for l in pathmatcher:
    # Our list element.
    for s in l:
        k, v = s.split('=')
        pathMatcherDict[k] = v
# Path rules are a bit different, since we have to check to see if we have more
# than 1.
# First count how many path rule declarations we have.
c = 0
for l in pathrules:
    for s in l:
        c += 1
if(c > 2):
    # We have multiple path rules, proceed with the below list form of the
    # nested loop.
    pathRulesDicts = list()
    d = dict()  # To hold temporary values.
    c = 1  # A counter.
    for l in pathrules:
        for s in l:
            k, v = s.split('=')
            d[k] = v
            if (c % 2 == 0):
                # We have a full path rule pair, so append to the list.
                pathRulesDicts.append(d)
                d = dict()
            c += 1  # Increment our counter.
else:
    # Assume a single pair (path/service).
    pathRulesDict = dict()
    for l in pathrules:
        for s in l:
            k, v = s.split('=')
            pathRulesDict[k] = v
# Now we start building the actual URL map, instantiate and load the YAML
# payload.
y = YAML()
with open(file) as f:
    payload = y.load(f.read())
"""
    Now is where we start building the actual parts of the URL map (host rule/path matcher/path rule (s)), based on the dictionaries and such that were built above.
    """
hostrule = build_hostrule(hostRuleDict['hosts'], hostRuleDict['pathMatcher'])
matcher = build_pathmatcher(
    pathMatcherDict['name'], pathMatcherDict['defaultService'])
"""
And we finally get to path rules. This will be a fun one, since we have to check which which pathRules related variable is set; the dictionary or the list of dictionaries. If the former, we can just call build_pathrules and pass it the singular path rule and move on with life. If we instead have the dictionary list, we have to loop through the path rule entries and call build_pathrule for each one, then add each generated path rule to the path matcher.
"""
if('pathRulesDict' in globals()):
    # We only have a singular path rule.
    pathRulesSingle = build_pathrule(
        pathRulesDict['path'], pathRulesDict['service'])
# Append any path rules we have to our path matcher.
# How many path rules do we have?
matcher['pathRules'] = list()
if('pathRulesSingle' in globals()):
    # We only have one.
    matcher['pathRules'].append(pathRulesSingle)
elif('pathRulesDicts' in globals()):
    # We have multiple path rules.
    for p in pathRulesDicts:
        rule = build_pathrule(p['path'], p['service'])
        matcher['pathRules'].append(rule)
# Now we start inserting actual things into our URL map
# (it was read into the payload variable above).
# First set our various rule insertion points.
hostRulesInsertionPoint = len(payload['hostRules'])+1
pathMatchersInsertionPoint = len(payload['pathMatchers'])+1
# Insert all the things!
# Figure out what actually needs inserting first.
# Check to see if a hostrule already exists for this host.
for host in payload['hostRules']:
    if(hostrule['hosts'][0] in host['hosts'][0]):
        # Found an existing host rule, so set a flag variable.
        hostrule_exists=1
        break
    else:
        hostrule_exists=0
# Now check for preexisting pathMatchers.
c=0
for pathmatcher in payload['pathMatchers']:
    if(matcher['name'] in pathmatcher['name']):
        # Found an existing matcher, set a flag variable.
        pathmatcher_exists=1
        break
    else:
        pathmatcher_exists=0
    c += 1
if(hostrule_exists == 1):
    print("A host rule for this host already exists, will not add a new one.")
else:
    payload['hostRules'].insert(hostRulesInsertionPoint, hostrule)
if(pathmatcher_exists == 1):
    # Found an existing pathMatcher, append any defined pathRules to it.
    print("This pathMatcher is already defined, will append any defined pathRules to this pathMatcher.")
    for pathrule in matcher['pathRules']:
        payload['pathMatchers'][c]['pathRules'].append(pathrule)
else:
    payload['pathMatchers'].insert(pathMatchersInsertionPoint, matcher)            


# Finally time to write out our payload.
with open(file, 'w') as f:
    y.dump(payload, f)
print("Payload has been written, exiting.")
sys.exit(0)
