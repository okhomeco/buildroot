#!/usr/bin/env python3
#
# Copyright 2017 The Dart project authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Usage: tools/dart/create_updated_flutter_deps.py [-d dart/DEPS] [-f flutter/DEPS]
#
# This script parses existing flutter DEPS file, identifies all 'dart_' prefixed
# dependencies, looks up revision from dart DEPS file, updates those dependencies
# and rewrites flutter DEPS file.

import argparse
import os
import sys

DART_SCRIPT_DIR = os.path.dirname(sys.argv[0])
DART_ROOT = os.path.realpath(os.path.join(DART_SCRIPT_DIR, '../../third_party/dart'))
FLUTTER_ROOT = os.path.realpath(os.path.join(DART_SCRIPT_DIR, '../../flutter'))

class VarImpl(object):
  def __init__(self, local_scope):
    self._local_scope = local_scope

  def Lookup(self, var_name):
    """Implements the Var syntax."""
    if var_name in self._local_scope.get("vars", {}):
      return self._local_scope["vars"][var_name]
    if var_name == 'host_os':
      return 'linux' # assume some default value
    if var_name == 'host_cpu':
      return 'x64' # assume some default value
    raise Exception("Var is not defined: %s" % var_name)


def ParseDepsFile(deps_file):
  local_scope = {}
  var = VarImpl(local_scope)
  global_scope = {
    'Var': var.Lookup,
    'deps_os': {},
  }
  # Read the content.
  with open(deps_file, 'r') as fp:
    deps_content = fp.read()

  # Eval the content.
  exec(deps_content, global_scope, local_scope)

  return (local_scope.get('vars', {}), local_scope.get('deps', {}))

def ParseArgs(args):
  args = args[1:]
  parser = argparse.ArgumentParser(
      description='A script to generate updated dart dependencies for flutter DEPS.')
  parser.add_argument('--dart_deps', '-d',
      type=str,
      help='Dart DEPS file.',
      default=os.path.join(DART_ROOT, 'DEPS'))
  parser.add_argument('--flutter_deps', '-f',
      type=str,
      help='Flutter DEPS file.',
      default=os.path.join(FLUTTER_ROOT, 'DEPS'))
  return parser.parse_args(args)

def Main(argv):
  args = ParseArgs(argv)
  (new_vars, new_deps) = ParseDepsFile(args.dart_deps)
  (old_vars, old_deps) = ParseDepsFile(args.flutter_deps)

  updated_vars = {}

  # Collect updated dependencies
  for (k,v) in sorted(old_vars.items()):
    if k not in ('dart_revision', 'dart_git') and k.startswith('dart_'):
      dart_key = k[len('dart_'):]
      if dart_key in new_vars:
        updated_revision = new_vars[dart_key].lstrip('@') if dart_key in new_vars else v
        updated_vars[k] = updated_revision

  # Write updated DEPS file to a side
  updatedfilename = args.flutter_deps + ".new"
  updatedfile = open(updatedfilename, "w")
  file = open(args.flutter_deps)
  lines = file.readlines()
  i = 0
  while i < len(lines):
    updatedfile.write(lines[i])
    if lines[i].startswith("  'dart_revision':"):
      i = i + 2
      updatedfile.writelines([
        '\n',
        '  # WARNING: DO NOT EDIT MANUALLY\n',
        '  # The lines between blank lines above and below are generated by a script. See create_updated_flutter_deps.py\n'])
      while i < len(lines) and len(lines[i].strip()) > 0:
        i = i + 1
      for (k, v) in sorted(updated_vars.items()):
        updatedfile.write("  '%s': '%s',\n" % (k, v))
      updatedfile.write('\n')

    elif lines[i].startswith("  # WARNING: Unused Dart dependencies"):
      updatedfile.write('\n')
      i = i + 1
      while i < len(lines) and (lines[i].startswith("  # WARNING: end of dart dependencies") == 0):
        i = i + 1
      for (k, v) in sorted(old_deps.items()):
        if (k.startswith('src/third_party/dart/')):
          for (dart_k, dart_v) in (list(new_deps.items())):
            dart_k_suffix = dart_k[len('sdk/') if dart_k.startswith('sdk/') else 0:]
            if (k.endswith(dart_k_suffix)):
              if (isinstance(dart_v, str)):
                updated_value = dart_v.replace(new_vars["dart_git"], "Var('dart_git') + '/")
                updated_value = updated_value.replace(old_vars["chromium_git"], "Var('chromium_git') + '")

                plain_v = dart_k[dart_k.rfind('/') + 1:]
                # This dependency has to be special-cased here because the
                # repository name is not the same as the directory name.
                if plain_v == "quiver":
                  plain_v = "quiver-dart"
                if ('dart_' + plain_v + '_tag' in updated_vars):
                  updated_value = updated_value[:updated_value.rfind('@')] + "' + '@' + Var('dart_" + plain_v + "_tag')"
                elif ('dart_' + plain_v + '_rev' in updated_vars):
                  updated_value = updated_value[:updated_value.rfind('@')] + "' + '@' + Var('dart_" + plain_v + "_rev')"
                else:
                  updated_value = updated_value + "'"
              else:
                # Non-string values(dicts) copy verbatim, keeping them sorted
                # to ensure stable ordering of items.
                updated_value = dict(sorted(dart_v.items()))

              updatedfile.write("  '%s':\n   %s,\n\n" % (k, updated_value))
              break
      updatedfile.write(lines[i])
    i = i + 1

  # Rename updated DEPS file into a new DEPS file
  os.remove(args.flutter_deps)
  os.rename(updatedfilename, args.flutter_deps)

  return 0

if __name__ == '__main__':
  sys.exit(Main(sys.argv))
