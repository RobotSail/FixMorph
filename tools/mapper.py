from common import definitions, values
from common.utilities import execute_command, error_exit, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import emitter, logger, finder, converter, writer, parallel
from ast import ast_generator
import sys

BREAK_LIST = [",", " ", " _", ";", "\n"]


def map_ast_from_source(source_a, source_b, script_file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_generator.generate_ast_script(source_a, source_b, script_file_path, True)
    mapping = dict()
    with open(script_file_path, 'r', encoding='utf8', errors="ignore") as script_file:
        script_lines = script_file.readlines()
        for script_line in script_lines:
            if "Match" in script_line:
                node_id_a = int(((script_line.split(" to ")[0]).split("(")[1]).split(")")[0])
                node_id_b = int(((script_line.split(" to ")[1]).split("(")[1]).split(")")[0])
                mapping[node_id_b] = node_id_a
    return mapping


def generate_map(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    emitter.normal("\tsource: " + file_a)
    emitter.normal("\ttarget: " + file_b)
    emitter.normal("\tgenerating ast map")
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -dump-matches "
        if values.DONOR_REQUIRE_MACRO:
            command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
        if values.TARGET_REQUIRE_MACRO:
            command += " " + values.TARGET_PRE_PROCESS_MACRO + " "
        command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        # command += "| grep '^Match ' "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating map: " + output_file)


def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content) - 1:
                if content[i] == "\\":
                    i += 2
                elif content[i] == "\"":
                    i += 1
                    break
                else:
                    i += 1
            prefix = content[:i]
            rest = content[i:].split(separator)
            node1 = prefix + rest[0]
            node2 = separator.join(rest[1:])
            return [node1, node2]
        i += 1
    # If all the above fails (it shouldn't), hope for some luck:
    nodes = content.split(separator)
    half = len(nodes) // 2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]


def generate_ast_map(generated_script_files):
    ast_map_info = dict()
    if len(generated_script_files) == 0:
        emitter.normal("\t -nothing-to-do")
    else:
        ast_map_info_local = generate_local_reference(generated_script_files)
        generate_global_reference(generated_script_files)
        ast_map_info = ast_map_info_local

        # extend namespace mapping using global reference
        emitter.sub_sub_title("merging local and global references")
        for vector_pair in values.map_namespace_global:
            map_global = values.map_namespace_global[vector_pair]
            map_local = values.map_namespace_local[vector_pair]
            map_merged = map_local
            for name_a in map_global:
                if "(" not in name_a:
                    continue
                if name_a not in map_merged:
                    map_merged[name_a] = map_global[name_a]
            values.map_namespace[vector_pair] = map_merged

        writer.write_var_map(map_merged, definitions.FILE_NAMESPACE_MAP)

    return ast_map_info


def generate_global_reference(generated_script_files):
    variable_map_info = dict()
    if len(generated_script_files) == 0:
        emitter.normal("\t -nothing-to-do")
    else:
        emitter.sub_sub_title("generating map using global reference")
        for file_list, generated_data in generated_script_files.items():
            slice_file_a = file_list[0]
            slice_file_c = file_list[2]
            vector_source_a = get_source_name_from_slice(slice_file_a)
            vector_source_c = get_source_name_from_slice(slice_file_c)

            map_file_name = definitions.DIRECTORY_OUTPUT + "/" + slice_file_a.split("/")[-1].replace(".slice", "") + ".map"
            if not values.CONF_USE_CACHE:
                generate_map(vector_source_a, vector_source_c, map_file_name)
            ast_node_map = parallel.get_mapping(map_file_name)
            emitter.data(ast_node_map)
            ast_node_map = parallel.extend_mapping(ast_node_map, vector_source_a, vector_source_c)
            emitter.data(ast_node_map)
            refined_var_map = parallel.derive_namespace_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            values.map_namespace_global[(vector_source_a, vector_source_c)] = refined_var_map
            writer.write_var_map(refined_var_map, definitions.FILE_NAMESPACE_MAP_GLOBAL)
            method_invocation_map = extend_method_invocation_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            emitter.data("method invocation map", method_invocation_map)
            values.Method_ARG_MAP_GLOBAL[(vector_source_a, vector_source_c)] = method_invocation_map
            function_map = extend_function_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            emitter.data("function map", function_map)
            values.FUNCTION_MAP_GLOBAL[(vector_source_a, vector_source_c)] = function_map

            variable_map_info[file_list] = ast_node_map
            # variable_map_info[file_list] = dict()
            # variable_map_info[file_list]['ast-map'] = ast_node_map
            # variable_map_info[file_list]['var-map'] = var_map
    return variable_map_info


def generate_local_reference(generated_script_files):
    variable_map_info = dict()
    if len(generated_script_files) == 0:
        emitter.normal("\t -nothing-to-do")
    else:
        emitter.sub_sub_title("generating map using local reference")
        for file_list, generated_data in generated_script_files.items():
            slice_file_a = file_list[0]
            slice_file_c = file_list[2]
            vector_source_a = get_source_name_from_slice(slice_file_a)
            vector_source_c = get_source_name_from_slice(slice_file_c)

            backup_file_orig(vector_source_a)
            backup_file_orig(vector_source_c)
            replace_file(slice_file_a, vector_source_a)
            replace_file(slice_file_c, vector_source_c)

            map_file_name = definitions.DIRECTORY_OUTPUT + "/" + slice_file_a.split("/")[-1] + ".map"
            if not values.CONF_USE_CACHE:
                generate_map(vector_source_a, vector_source_c, map_file_name)
            ast_node_map = parallel.get_mapping(map_file_name)
            emitter.data(ast_node_map)
            ast_node_map = parallel.extend_mapping(ast_node_map, vector_source_a, vector_source_c)
            emitter.data(ast_node_map)
            refined_var_map = parallel.derive_namespace_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            values.map_namespace_local[(vector_source_a, vector_source_c)] = refined_var_map
            writer.write_var_map(refined_var_map, definitions.FILE_NAMESPACE_MAP_LOCAL)
            method_invocation_map = extend_method_invocation_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            emitter.data("method invocation map", method_invocation_map)
            values.Method_ARG_MAP_LOCAL[(vector_source_a, vector_source_c)] = method_invocation_map
            function_map = extend_function_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            emitter.data("function map", function_map)
            values.FUNCTION_MAP_LOCAL[(vector_source_a, vector_source_c)] = function_map

            restore_file_orig(vector_source_a)
            restore_file_orig(vector_source_c)
            variable_map_info[file_list] = ast_node_map
            # variable_map_info[file_list] = dict()
            # variable_map_info[file_list]['ast-map'] = ast_node_map
            # variable_map_info[file_list]['var-map'] = var_map
    return variable_map_info


def extend_function_map(ast_node_map, source_a, source_c, slice_file_a):
    function_map = dict()
    emitter.normal("\tderiving function signature map")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

        if ast_node_a and ast_node_c:
            node_type_a = ast_node_a['type']
            node_type_c = ast_node_c['type']
            if node_type_a in ["FunctionDecl"] and node_type_c in ["FunctionDecl"]:
                children_a = ast_node_a["children"]
                children_c = ast_node_c["children"]
                if len(children_a) < 1 or len(children_c) < 1:
                    continue
                method_signature_a = children_a[0]
                method_signature_c = children_c[0]

                method_name_a = ast_node_a["identifier"]
                parameter_list_a = method_signature_a['children']
                parameter_list_c = method_signature_c['children']
                arg_operation = []
                for i in range(1, len(parameter_list_a)):
                    node_txt_a = parameter_list_a[i]["type"] + "(" + str(parameter_list_a[i]["id"]) + ")"
                    if node_txt_a in ast_node_map.keys():
                        node_txt_c = ast_node_map[node_txt_a]
                        node_id_c = int(str(node_txt_c).split("(")[1].split(")")[0])
                        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, node_id_c)
                        if ast_node_c in parameter_list_c:
                            arg_operation.append((definitions.MATCH, i, parameter_list_c.index(ast_node_c)))
                        else:
                            arg_operation.append((definitions.DELETE, i))
                    else:
                        arg_operation.append((definitions.DELETE, i))
                for i in range(1, len(parameter_list_c)):
                    node_txt_c = parameter_list_c[i]["type"] + "(" + str(parameter_list_c[i]["id"]) + ")"
                    if node_txt_c not in ast_node_map.values():
                        arg_operation.append((definitions.INSERT, i, converter.get_node_value(parameter_list_c[i])))
                function_map[method_name_a] = arg_operation
    return function_map


def extend_method_invocation_map(ast_node_map, source_a, source_c, slice_file_a):
    method_invocation_map = dict()
    emitter.normal("\tderiving method invocation map")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

        if ast_node_a and ast_node_c:
            node_type_a = ast_node_a['type']
            node_type_c = ast_node_c['type']
            if node_type_a in ["CallExpr"] and node_type_c in ["CallExpr"]:
                children_a = ast_node_a["children"]
                children_c = ast_node_c["children"]
                if len(children_a) < 1 or len(children_c) < 1 or len(children_a) == len(children_c):
                    continue
                method_name = children_a[0]["value"]

                arg_operation = []
                for i in range(1, len(children_a)):
                    node_txt_a = children_a[i]["type"] + "(" + str(children_a[i]["id"]) + ")"
                    if node_txt_a in ast_node_map.keys():
                        node_txt_c = ast_node_map[node_txt_a]
                        node_id_c = int(str(node_txt_c).split("(")[1].split(")")[0])
                        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, node_id_c)
                        if ast_node_c in children_c:
                            arg_operation.append((definitions.MATCH, i, children_c.index(ast_node_c)))
                        else:
                            arg_operation.append((definitions.DELETE, i))
                    else:
                        arg_operation.append((definitions.DELETE, i))
                for i in range(1, len(children_c)):
                    node_txt_c = children_c[i]["type"] + "(" + str(children_c[i]["id"]) + ")"
                    if node_txt_c not in ast_node_map.values():
                        arg_operation.append((definitions.INSERT, i, converter.get_node_value(children_c[i])))

                method_invocation_map[method_name] = arg_operation
    return method_invocation_map


# adjust the mapping via anti-unification
def extend_mapping(ast_node_map, map_file_name, source_a, source_c):
    emitter.normal("\tupdating ast map using anti-unification")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    with open(map_file_name, 'r') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == definitions.MATCH:
                try:
                    node_a, node_c = clean_parse(content, definitions.TO)
                    ast_node_id_a = int(str(node_a).split("(")[1].split(")")[0])
                    ast_node_id_c = int(str(node_c).split("(")[1].split(")")[0])
                    ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
                    ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

                    au_pairs = anti_unification(ast_node_a, ast_node_c)
                    for au_pair_key in au_pairs:
                        au_pair_value = au_pairs[au_pair_key]
                        ast_node_map[au_pair_key] = au_pair_value
                except Exception as exception:
                    error_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return ast_node_map


def anti_unification(ast_node_a, ast_node_c):
    au_pairs = dict()
    waiting_list_a = [ast_node_a]
    waiting_list_c = [ast_node_c]

    while len(waiting_list_a) != 0 and len(waiting_list_c) != 0:
        current_a = waiting_list_a.pop()
        current_c = waiting_list_c.pop()

        children_a = current_a["children"]
        children_c = current_c["children"]

        # do not support anti-unification with different number of children yet
        if len(children_a) != len(children_c):
            continue

        length = len(children_a)
        for i in range(length):
            child_a = children_a[i]
            child_c = children_c[i]
            if child_a["type"] == child_c["type"]:
                waiting_list_a.append(child_a)
                waiting_list_c.append(child_c)
            else:
                key = child_a["type"] + "(" + str(child_a["id"]) + ")"
                value = child_c["type"] + "(" + str(child_c["id"]) + ")"
                au_pairs[key] = value

    return au_pairs

