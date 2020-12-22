#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import os
from common import values, definitions
from common.utilities import get_code, error_exit, execute_command
from ast import generator as ASTGenerator
from tools import extractor, oracle, logger, filter, emitter, transformer


def slice_source_file(source_path, segment_code, segment_identifier, project_path, use_macro=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_tree = ASTGenerator.get_ast_json(source_path, use_macro, True)
    segment_type = values.segment_map[segment_code]
    ast_script = list()
    source_relative_path = source_path.replace(project_path, ".")
    segment_found = False
    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier != segment_identifier:
                if 'file' in ast_node.keys():
                    if ast_node['file'] == source_path.replace(project_path, "")[1:]:
                        ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")
            else:
                segment_found = True

    if not segment_found:
        emitter.information("Slice not created")
        return False

    # print(ast_script)
    output_file_name = "." + segment_code + "." + segment_identifier + ".slice"
    output_file_path = source_path + output_file_name
    ast_script_path = definitions.DIRECTORY_OUTPUT + "/" + output_file_path.split("/")[-1] + ".ast"
    if ast_script:
        transformer.transform_source_file(source_path, ast_script, output_file_path, ast_script_path)
        if os.stat(output_file_path).st_size == 0:
            error_exit("Slice is empty")
    else:
        copy_command = "cp " + source_path + " " + output_file_path
        emitter.warning("\t\t[warning] AST script was empty, using full file")
        execute_command(copy_command)

    emitter.normal("\t\t\tcreated " + output_file_path)
    return segment_found
