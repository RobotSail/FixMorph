from app.common import definitions, values
from app.common.utilities import error_exit
from app.tools import identifier
from app.tools import parallel, emitter, finder, extractor, writer, logger
from app.ast import ast_generator

import sys


def evolve_definitions(missing_definition_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    missing_header_list = dict()
    missing_macro_list = dict()
    if not missing_definition_list:
        emitter.normal("\t-none-")
    ast_tree_b = None
    def_node_list = dict()
    for def_name in missing_definition_list:
        emitter.normal(def_name)
        macro_info = missing_definition_list[def_name]
        source_file = macro_info['source']
        target_file = macro_info['target']
        def_node_list = extractor.extract_macro_definitions(source_file)
        if not ast_tree_b:
            ast_tree_b = ast_generator.get_ast_json(source_file, use_macro=values.DONOR_REQUIRE_MACRO)
            def_node_list = extractor.extract_def_node_list(ast_tree_b)
        if def_name in def_node_list:
            def_node = def_node_list[def_name]
            if 'identifier' in def_node:
                identifier = def_node['identifier']
                if identifier == def_name:
                    if "file" in def_node:
                        def_file = def_node['file']
                        if def_file[-1] == "h":
                            header_file = def_file.split("/include/")[-1]
                            missing_header_list[header_file] = target_file
                            emitter.success("\t\tfound definition in: " + def_file)
                    else:
                        missing_macro_list[def_name] = missing_definition_list[def_name]
        else:
            missing_macro_list[def_name] = missing_definition_list[def_name]


        # def_insert_line = Finder.find_definition_insertion_point(target_file)
        # missing_macro_list = Identifier.identify_missing_macros_in_func(ast_node, function_source_file,
        #                                                             source_path_d)
        # missing_header_list = Identifier.identify_missing_headers(ast_node, source_path_d)
        #
    # print(missing_header_list)
    # print(missing_macro_list)
    return missing_header_list, missing_macro_list


def evolve_data_type(missing_data_type_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    missing_header_list = dict()
    missing_macro_list = dict()
    if not missing_data_type_list:
        emitter.normal("\t-none-")

    for data_type in missing_data_type_list:
        emitter.normal(data_type)
        data_type_info = missing_data_type_list[data_type]
        ast_node = data_type_info['ast-node']
        def_start_line = int(ast_node['start line'])
        def_end_line = int(ast_node['end line'])
        source_file = ast_node['file']
        target_file = data_type_info['target']

        # missing_macro_list = Identifier.identify_missing_macros_in_func(ast_node, function_source_file,
        #                                                             source_path_d)
        missing_header_list = identifier.identify_missing_headers(ast_node, target_file)

    return missing_header_list, missing_macro_list


def evolve_functions(missing_function_list, depth_level):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_function_list:
        emitter.normal("\t-none-")
    def_insert_point = ""
    missing_header_list = dict()
    missing_macro_list = dict()
    dependent_function_name_list = list()
    dependent_missing_function_list = dict()
    filtered_missing_function_list = dict()
    for function_name in missing_function_list:
        info = missing_function_list[function_name]
        node_id = info['node_id']
        source_path = info['source_a']
        target_path = info['source_d']
        emitter.normal(function_name)
        ast_map_key = info['ast-key']
        ast_global_a = ast_generator.get_ast_json(source_path, values.DONOR_REQUIRE_MACRO, regenerate=True)
        ast_global_c = ast_generator.get_ast_json(target_path, values.TARGET_REQUIRE_MACRO, regenerate=True)
        mapping = None
        if values.CONF_PATH_B not in source_path:
            if values.DEFAULT_OPERATION_MODE == 0:
                mapping = parallel.generate_method_invocation_map(source_path, target_path,
                                                                  ast_global_a, ast_global_c, function_name)
                if not mapping:
                    mapping = parallel.generate_function_signature_map(source_path, target_path,
                                                                       ast_global_a, ast_global_c, function_name)

        # if no mapping found add function for transplantation list
        vector_pair = (ast_map_key[0], ast_map_key[2])
        refined_var_map = values.map_namespace_global[vector_pair]
        if mapping:
            for method_name_a in mapping:
                candidate_list = mapping[method_name_a]
                best_score = 0
                method_name_c = None
                transformation_c = None
                for candidate_name in candidate_list:
                    match_score, transformation = candidate_list[candidate_name]
                    if match_score > best_score:
                        best_score = match_score
                        method_name_c = candidate_name
                        transformation_c = transformation
                # print(transformation_c)
                if values.IS_LINUX_KERNEL:
                    if best_score > 1:
                        refined_var_map[method_name_a + "("] = method_name_c + "("
                    else:
                        if function_name + "(" in refined_var_map:
                            del refined_var_map[function_name + "("]
                        mapping = None
                else:
                    refined_var_map[method_name_a + "("] = method_name_c + "("
            writer.write_var_map(refined_var_map, definitions.FILE_NAMESPACE_MAP_LOCAL)

        if not mapping:
            # ast_map_b = ast_generator.get_ast_json(source_path_b)
            function_ref_node_id = int(info['ref_node_id'])
            function_ref_node = finder.search_ast_node_by_id(ast_global_a, function_ref_node_id)
            function_def_node = finder.search_ast_node_by_id(ast_global_a, int(node_id))
            function_source_file = function_def_node['file']
            found_header_file = False
            if function_source_file[-1] == "h":
                header_file = function_source_file
                clone_header_file = finder.find_clone(header_file)
                if clone_header_file:
                    ast_header = ast_generator.get_ast_json(clone_header_file, values.DONOR_REQUIRE_MACRO,
                                                                regenerate=True)
                    header_func_list = extractor.extract_function_node_list(ast_header)
                    if function_name in header_func_list:
                        clone_header_file = clone_header_file.split("/include/")[-1]
                        found_header_file = True
                        missing_header_list[clone_header_file] = target_path
                else:
                    if "include" in function_source_file:
                        header_file = function_source_file.split("/include/")[-1]
                    else:
                        header_file = function_source_file.split("/")[-1]
                    clone_header_file = finder.find_clone(header_file)
                    if clone_header_file:
                        ast_header = ast_generator.get_ast_json(clone_header_file, values.DONOR_REQUIRE_MACRO,
                                                                regenerate=True)
                        header_func_list = extractor.extract_function_node_list(ast_header)
                        if function_name in header_func_list:
                            clone_header_file = clone_header_file.split("/include/")[-1]
                            found_header_file = True
                            missing_header_list[clone_header_file] = target_path

            if not found_header_file:
                filtered_missing_function_list[function_name] = info

                function_node, function_source_file = extractor.extract_complete_function_node(function_def_node,
                                                                                               source_path)
                missing_def_list, dependent_function_name_list = identifier.identify_missing_definitions(function_node,
                                                                                                         missing_function_list)

                missing_macro_list = identifier.identify_missing_macros_in_func(function_node, function_source_file,
                                                                                target_path)
                missing_header_list = identifier.identify_missing_headers(function_node, target_path)

                for dep_fun_name in dependent_function_name_list:
                    dep_info = dict()
                    dep_source_tree = ast_generator.get_ast_json(function_source_file, values.DONOR_REQUIRE_MACRO, regenerate=True)
                    func_list_dep_source = extractor.extract_function_node_list(dep_source_tree)
                    if dep_fun_name not in func_list_dep_source:
                        continue
                    dependent_function_node = extractor.extract_function_node_list(dep_source_tree)[dep_fun_name]
                    dep_info['node_id'] = dependent_function_node['id']
                    dep_info['ref_node_id'] = function_node['id']
                    dep_info['source_a'] = function_source_file
                    dep_info['source_d'] = target_path
                    dep_info['ast-key'] = ast_map_key
                    dependent_missing_function_list[dep_fun_name] = dep_info

            emitter.success("\t\tfound definition in: " + function_source_file)
            # print(function_name)
    if dependent_function_name_list and depth_level > 1:
        dep_header_list, dep_macro_list, dep_missing_function_list = evolve_functions(dependent_missing_function_list, 
                                                                                       depth_level - 1)
        missing_macro_list.update(dep_macro_list)
        missing_header_list.update(dep_header_list)
        filtered_missing_function_list.update(dep_missing_function_list)
    
    return missing_header_list, missing_macro_list, filtered_missing_function_list


def evolve_code(slice_file_list, source_file_list, instruction_list, seg_id_a, seg_id_c, seg_code,
                ast_tree_global_a, ast_tree_global_b, ast_tree_global_c):

    missing_function_list = dict()
    missing_var_list = dict()
    missing_global_var_list = dict()
    missing_macro_list = dict()
    missing_label_list = dict()
    missing_header_list = dict()
    missing_data_type_list = dict()
    slice_file_a, slice_file_b, slice_file_c, slice_file_d = slice_file_list
    source_file_a, source_file_b, source_file_c, source_file_d = source_file_list
    ast_map_key = (slice_file_a, slice_file_b, slice_file_c)
    namespace_map_key = (slice_file_a, slice_file_c)

    if values.DONOR_REQUIRE_MACRO:
        values.PRE_PROCESS_MACRO = values.DONOR_PRE_PROCESS_MACRO
    # ast_tree_local_a = ast_generator.get_ast_json(file_a, values.DONOR_REQUIRE_MACRO, True)
    ast_tree_local_b = ast_generator.get_ast_json(source_file_b, values.DONOR_REQUIRE_MACRO, True)

    if values.TARGET_REQUIRE_MACRO:
        values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO
    ast_tree_local_c = ast_generator.get_ast_json(source_file_c, values.TARGET_REQUIRE_MACRO, True)


    # Check for an edit script
    script_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(seg_id_c) + "_script"
    syntax_error_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(seg_id_c) + "_syntax_errors"
    neighborhood_a = extractor.extract_neighborhood(source_file_a, seg_code, seg_id_a, values.DONOR_REQUIRE_MACRO)
    neighborhood_b = extractor.extract_neighborhood(source_file_b, seg_code, seg_id_a, values.DONOR_REQUIRE_MACRO)
    neighborhood_c = extractor.extract_neighborhood(source_file_c, seg_code, seg_id_c, values.TARGET_REQUIRE_MACRO)
    decl_list_c = extractor.extract_decl_node_list(neighborhood_c)
    # ref_list = extractor.extract_reference_node_list(neighborhood_c)
    if not neighborhood_a or not neighborhood_c:
        emitter.error("[error] neighborhood not found")
        emitter.error("Seg Code: " + str(seg_code))
        emitter.error("PA: " + str(source_file_a) + "-" + str(seg_id_a))
        emitter.error("PB: " + str(source_file_b) + "-" + str(seg_id_a))
        emitter.error("PC: " + str(source_file_c) + "-" + str(seg_id_c))
        error_exit("unable to evolve the code")

    var_map = values.map_namespace_global[(slice_file_a, slice_file_c)]
    script_lines = list()
    segment_type = values.segment_map[seg_code]
    count = 0

    if values.Project_A.header_list:
        if source_file_a in values.Project_A.header_list:
            if "added" in values.Project_A.header_list[source_file_a]:
                new_header_file_list = values.Project_A.header_list[source_file_a]['added']
                for header_file in new_header_file_list:
                    header_file = header_file.replace("#include", "").replace("\n", "").replace("<", "").replace(">", "").strip()
                    values.missing_header_list[header_file] = source_file_d

    for instruction in instruction_list:
        count = count + 1
        # Emitter.normal("\t[action]transplanting code segment " + str(count))
        emitter.special("\t\t" + str(instruction))
        check_node = None
        relative_pos = 0
        if "Insert" in instruction:
            check_node_id = instruction.split("(")[1].split(")")[0]
            check_node = finder.search_ast_node_by_id(ast_tree_local_b, int(check_node_id))
            if check_node['type'] == "DeclStmt":
                var_node = check_node['children'][0]
                var_name = var_node['identifier']
                if var_name in decl_list_c.keys():
                    continue
            relative_pos = instruction.split(" into ")[-1].replace("\n", "")
        elif "Replace" in instruction:
            target_node_id = instruction.split(" with ")[0].split("(")[1].split(")")[0]
            target_node = finder.search_ast_node_by_id(ast_tree_local_c, int(target_node_id))
            target_parent_node_id = int(target_node['parent_id'])
            target_parent_node = finder.search_ast_node_by_id(ast_tree_local_c, int(target_parent_node_id))
            child_index = 0
            for child_node in target_parent_node['children']:
                if int(child_node['id']) == int(target_node_id):
                    relative_pos = child_index
                    break
                relative_pos = relative_pos + 1
            relative_pos = target_parent_node['type'] + "(" + str(target_parent_node_id) + ") at " + str(relative_pos)
            check_node_id = instruction.split(" with ")[1].split("(")[1].split(")")[0]
            check_node = finder.search_ast_node_by_id(ast_tree_local_b, int(check_node_id))

        elif "Update" in instruction:
            target_node_id = instruction.split(" with ")[0].split("(")[1].split(")")[0]
            target_node = finder.search_ast_node_by_id(ast_tree_local_c, int(target_node_id))
            target_parent_node_id = int(target_node['parent_id'])
            target_parent_node = finder.search_ast_node_by_id(ast_tree_local_c, int(target_parent_node_id))
            child_index = 0
            for child_node in target_parent_node['children']:
                if int(child_node['id']) == int(target_node_id):
                    relative_pos = child_index
                    break
                relative_pos = relative_pos + 1
            relative_pos = target_parent_node['type'] + "(" + str(target_parent_node_id) + ") at " + str(relative_pos)
            check_node_id = instruction.split(" to ")[1].split("(")[1].split(")")[0]
            check_node = finder.search_ast_node_by_id(ast_tree_local_b, int(check_node_id))
            if check_node['type'] == "IfStmt":
                check_node['children'] = [check_node['children'][0]]

        elif "Delete" in instruction:
            check_node = None

        if check_node:

            missing_function_list.update(identifier.identify_missing_functions(check_node,
                                                                               source_file_b,
                                                                               source_file_d,
                                                                               ast_tree_global_a,
                                                                               ast_tree_global_b,
                                                                               ast_tree_global_c,
                                                                               ast_map_key))

            missing_macro_list.update(identifier.identify_missing_macros(check_node,
                                                                         source_file_b,
                                                                         source_file_d,
                                                                         namespace_map_key,
                                                                         ast_tree_global_c
                                                                         ))

            missing_var_list.update(identifier.identify_missing_var(neighborhood_a,
                                                                    neighborhood_b,
                                                                    neighborhood_c,
                                                                    check_node,
                                                                    source_file_b,
                                                                    source_file_d,
                                                                    var_map,
                                                                    relative_pos
                                                                    ))

            missing_data_type_list.update(identifier.identify_missing_data_types(ast_tree_global_a,
                                                                                 ast_tree_global_b,
                                                                                 ast_tree_global_c,
                                                                                 check_node,
                                                                                 source_file_b,
                                                                                 source_file_d,
                                                                                 var_map
                                                                                 ))
            if segment_type in ["FunctionDecl", "Macro"]:
                missing_label_list.update(identifier.identify_missing_labels(neighborhood_a,
                                                                             neighborhood_b,
                                                                             neighborhood_c,
                                                                             check_node,
                                                                             source_file_b,
                                                                             var_map
                                                                             ))

        script_lines.append(instruction)
    # print(missing_var_list)
    target_ast = None
    if neighborhood_c['type'] in ["FunctionDecl", "RecordDecl"]:
        target_ast = neighborhood_c['children'][1]
        local_position_c = target_ast['type'] + "(" + str(target_ast['id']) + ") at " + str(0)

        for var in missing_var_list:
            # print(var)
            var_info = missing_var_list[var]
            if "pre-exist" not in var_info:
                continue
            if var_info['is_global']:
                missing_global_var_list[var] = var_info
                continue
            if not var_info['pre-exist'] or var_info['map-exist']:
                continue
            if "ast-node" in var_info.keys():
                ast_node = var_info['ast-node']
                # not sure why the if is required
                # if "ref_type" in ast_node.keys():
                node_id_a = ast_node['id']
                node_id_b = node_id_a
                instruction = "Insert " + ast_node['type'] + "(" + str(node_id_b) + ")"
                instruction += " into " + local_position_c
                script_lines.insert(0, instruction + "\n")
                emitter.highlight("\t\tadditional variable added with instruction: " + instruction)
                if len(ast_node['children']) == 1:
                    decl_node_id = int(ast_node['parent_id'])
                    ref_node_id = int(var_info['ref-id'])
                    decl_node = finder.search_ast_node_by_id(ast_tree_local_b, int(decl_node_id))
                    scope_node_id = decl_node['parent_id']
                    scope_node = finder.search_ast_node_by_id(ast_tree_local_b, int(scope_node_id))
                    init_list = extractor.extract_initialization_node_list(scope_node, ast_node)
                    latest_node = None
                    for node in init_list:
                        node_id = int(node['id'])
                        if node_id >= ref_node_id:
                            break
                        latest_node = node
                    if latest_node:
                        relative_pos = var_info['rel-pos']
                        instruction = "Insert " + latest_node['type'] + "(" + str(latest_node['id']) + ")"
                        instruction += " into " + str(relative_pos)
                        script_lines.insert(1, instruction + "\n")
                        emitter.highlight("\t\tadditional initialization added with instruction: " + instruction)

            # elif "enum-value" in var_info.keys():
            #     var_map[var] = str(var_info['enum-value'])

        values.map_namespace_global[(source_file_a, source_file_c)] = var_map
        writer.write_var_map(var_map, definitions.FILE_NAMESPACE_MAP_LOCAL)
        if neighborhood_c['type'] in ["FunctionDecl"]:
            offset = len(target_ast['children']) - 1
            position_c = target_ast['type'] + "(" + str(target_ast['id']) + ") at " + str(offset)
            for label in missing_label_list:
                # print(var)
                label_info = missing_label_list[label]
                ast_node = label_info['ast-node']
                # not sure why the if is required
                # if "ref_type" in ast_node.keys():
                node_id_a = ast_node['id']
                node_id_b = node_id_a
                instruction = "Insert " + ast_node['type'] + "(" + str(node_id_b) + ")"
                instruction += " into " + position_c
                script_lines.insert(0, instruction + "\n")
                emitter.highlight("\t\tadditional label added with instruction: " + instruction)

    # with open(script_file_name, 'w') as script_file:
    #     for transformation_rule in script_lines:
    #         script_file.write(transformation_rule)

    emitter.success("\n\t\tSuccessful evolution")
    return missing_function_list, missing_macro_list, script_lines, missing_global_var_list, missing_data_type_list

