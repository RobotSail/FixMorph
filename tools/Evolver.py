from common import Definitions, Values
from common.Utilities import execute_command, error_exit, get_code, backup_file, show_partial_diff, backup_file_orig, restore_file_orig, replace_file, get_code_range
from tools import Emitter, Logger, Finder, Extractor, Identifier
from ast import Generator

import os
import sys


def evolve_definitions(missing_definition_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    missing_header_list = dict()
    missing_macro_list = dict()
    if not missing_definition_list:
        Emitter.normal("\t-none-")
    for def_name in missing_definition_list:
        Emitter.normal(def_name)
        macro_info = missing_definition_list[def_name]
        source_file = macro_info['source']
        target_file = macro_info['target']
        macro_def_list = Extractor.extract_macro_definitions(source_file)
        def_insert_line = Finder.find_definition_insertion_point(target_file)
        # missing_macro_list = Identifier.identify_missing_macros_in_func(ast_node, function_source_file,
        #                                                             source_path_d)
        # missing_header_list = Identifier.identify_missing_headers(ast_node, source_path_d)
        #
    return missing_header_list, missing_macro_list


def evolve_data_type(missing_data_type_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    missing_header_list = dict()
    missing_macro_list = dict()
    if not missing_data_type_list:
        Emitter.normal("\t-none-")

    for data_type in missing_data_type_list:
        Emitter.normal(data_type)
        data_type_info = missing_data_type_list[data_type]
        ast_node = data_type_info['ast-node']
        def_start_line = int(ast_node['start line'])
        def_end_line = int(ast_node['end line'])
        source_file = ast_node['file']
        target_file = data_type_info['target']

        # missing_macro_list = Identifier.identify_missing_macros_in_func(ast_node, function_source_file,
        #                                                             source_path_d)
        # missing_header_list = Identifier.identify_missing_headers(ast_node, source_path_d)
        #
    return missing_header_list, missing_macro_list


def evolve_functions(missing_function_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_function_list:
        Emitter.normal("\t-none-")
    def_insert_point = ""
    missing_header_list = dict()
    missing_macro_list = dict()
    for function_name in missing_function_list:
        info = missing_function_list[function_name]
        node_id = info['node_id']
        source_path_b = info['source_b']
        source_path_d = info['source_d']
        Emitter.normal(function_name)
        ast_map_b = Generator.get_ast_json(source_path_b)
        function_ref_node_id = int(info['ref_node_id'])
        function_ref_node = Finder.search_ast_node_by_id(ast_map_b, function_ref_node_id)
        function_def_node = Finder.search_ast_node_by_id(ast_map_b, int(node_id))
        function_node, function_source_file = Extractor.extract_complete_function_node(function_def_node,
                                                                                       source_path_b)
        missing_def_list = Identifier.identify_missing_definitions(function_node, missing_function_list)
        missing_macro_list = Identifier.identify_missing_macros_in_func(function_node, function_source_file,
                                                                        source_path_d)
        missing_header_list = Identifier.identify_missing_headers(function_node, source_path_d)
        # print(function_name)
    return missing_header_list, missing_macro_list


def evolve_code(file_a, file_b, file_c, instruction_list, seg_id_a, seg_id_c, seg_code):
    missing_function_list = dict()
    missing_var_list = dict()
    missing_macro_list = dict()
    missing_header_list = dict()
    missing_data_type_list = dict()

    if Values.DONOR_REQUIRE_MACRO:
        Values.PRE_PROCESS_MACRO = Values.DONOR_PRE_PROCESS_MACRO
    ast_map_a = Generator.get_ast_json(file_a, Values.DONOR_REQUIRE_MACRO, True)
    ast_map_b = Generator.get_ast_json(file_b, Values.DONOR_REQUIRE_MACRO, True)

    if Values.TARGET_REQUIRE_MACRO:
        Values.PRE_PROCESS_MACRO = Values.TARGET_PRE_PROCESS_MACRO
    ast_map_c = Generator.get_ast_json(file_c, Values.TARGET_REQUIRE_MACRO, True)

    file_d = str(file_c).replace(Values.Project_C.path, Values.Project_D.path)

    # Check for an edit script
    script_file_name = Definitions.DIRECTORY_OUTPUT + "/" + str(seg_id_c) + "_script"
    syntax_error_file_name = Definitions.DIRECTORY_OUTPUT + "/" + str(seg_id_c) + "_syntax_errors"
    neighborhood_a = Extractor.extract_neighborhood(file_a, seg_code, seg_id_a)
    neighborhood_c = Extractor.extract_neighborhood(file_c, seg_code, seg_id_c)

    with open(script_file_name, 'w') as script_file:
        count = 0
        for instruction in instruction_list:
            count = count + 1
            # Emitter.normal("\t[action]transplanting code segment " + str(count))
            check_node = None
            if "Insert" in instruction:
                check_node_id = instruction.split("(")[1].split(")")[0]
                check_node = Finder.search_ast_node_by_id(ast_map_b, int(check_node_id))

            elif "Replace" in instruction:
                check_node_id = instruction.split(" with ")[1].split("(")[1].split(")")[0]
                check_node = Finder.search_ast_node_by_id(ast_map_b, int(check_node_id))

            elif "Update" in instruction:
                check_node_id = instruction.split(" to ")[1].split("(")[1].split(")")[0]
                check_node = Finder.search_ast_node_by_id(ast_map_b, int(check_node_id))

            elif "Delete" in instruction:
                check_node = None

            if check_node:

                missing_function_list.update(Identifier.identify_missing_functions(ast_map_a,
                                                                                   check_node,
                                                                                   file_b,
                                                                                   file_d,
                                                                                   ast_map_c))

                missing_macro_list.update(Identifier.identify_missing_macros(check_node,
                                                                             file_b,
                                                                             file_d
                                                                             ))
                var_map = Values.VAR_MAP[(file_a, file_c)]
                missing_var_list.update(Identifier.identify_missing_var(neighborhood_a,
                                                                        neighborhood_c,
                                                                        check_node,
                                                                        file_b,
                                                                        var_map
                                                                        ))

            script_file.write(instruction + "\n")
        # print(missing_var_list)
        target_ast = None
        if neighborhood_c['type'] in ["FunctionDecl", "RecordDecl"]:
            target_ast = neighborhood_c['children'][1]
        position_c = target_ast['type'] + "(" + str(target_ast['id']) + ") at " + str(1)
        for var in missing_var_list:
            # print(var)
            var_info = missing_var_list[var]
            ast_node = var_info['ast-node']
            # not sure why the if is required
            # if "ref_type" in ast_node.keys():
            node_id_a = ast_node['id']
            node_id_b = node_id_a
            instruction = "Insert " + ast_node['type'] + "(" + str(node_id_b) + ")"
            instruction += " into " + position_c
            script_file.write(instruction + "\n")
            Emitter.highlight("\t\tadditional variable added with instruction: " + instruction)

    Emitter.success("\n\tSuccessful evolution")
    return missing_function_list, missing_macro_list
