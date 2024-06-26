#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys, os
from app.common.utilities import execute_command, error_exit, show_partial_diff, backup_file, get_code, definitions
from app.ast import ast_generator
from app.tools import emitter, finder, logger

FILE_SYNTAX_ERRORS = ""
FILENAME_BACKUP = "backup-syntax-fix"


def extract_goto_node(ast_node, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    node_type = str(ast_node["type"])
    goto_node_list = list()
    if node_type == "GotoStmt":
        goto_node_list.append(ast_node)
        return goto_node_list
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                goto_node_list += extract_goto_node(child_node, line_number)

    if node_type == "FunctionDecl":
        for goto_node in goto_node_list:
            start_line = int(goto_node['start line'])
            end_line = int(goto_node['end line'])
            # print(start_line, line_number, end_line)
            if start_line <= line_number <= end_line:
                return goto_node
    else:
        return goto_node_list


def extract_return_node(ast_node, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    node_type = str(ast_node["type"])
    return_node_list = list()
    if node_type == "ReturnStmt":
        return_node_list.append(ast_node)
        return return_node_list
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                return_node_list += extract_return_node(child_node, line_number)

    if node_type == "FunctionDecl":
        for return_node in return_node_list:
            start_line = int(return_node['start line'])
            end_line = int(return_node['end line'])
            # print(start_line, line_number, end_line)
            if start_line <= line_number <= end_line:
                return return_node
    else:
        return return_node_list


def replace_code(patch_code, source_path, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    if os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf8', errors="ignore") as source_file:
            content = source_file.readlines()
            content[line_number-1] = patch_code

    with open(source_path, 'w', encoding='utf8', errors="ignore") as source_file:
        source_file.writelines(content)


def fix_return_type(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing return type")
    line_number = int(source_location.split(":")[1])
    ast_map = ast_generator.get_ast_json(source_file)
    function_node = finder.search_function_node_by_loc(ast_map, int(line_number), source_file)
    return_node = extract_return_node(function_node, line_number)
    start_line = return_node['start line']
    end_line = return_node['end line']
    function_definition = function_node['value']
    function_name = function_node['identifier']

    function_return_type = (function_definition.replace(function_name, "")).split("(")[1]
    original_statement = ""
    if function_return_type.strip() == "void":
        new_statement = "return;\n"
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, start_line)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)
    elif function_return_type.strip() == "int":
        new_statement = "return -1;\n"
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, start_line)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)
    else:
        error_exit("NEW RETURN TYPE!")
    # check_syntax_errors()


def fix_label_error(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing label errors")
    line_number = int(source_location.split(":")[1])
    ast_map = ast_generator.get_ast_json(source_file)
    function_node = finder.search_function_node_by_loc(ast_map, int(line_number), source_file)
    goto_node = extract_goto_node(function_node, line_number)
    function_definition = function_node['value']
    function_name = function_node['identifier']
    function_return_type = (function_definition.replace(function_name, "")).split("(")[1]
    start_line = goto_node['start line']
    end_line = goto_node['end line']
    original_statement = ""
    if function_return_type.strip() == "void":
        new_statement = "return;\n"
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, start_line)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)
    elif function_return_type.strip() == "int":
        new_statement = "return -1;\n"
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, start_line)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)
    else:
        error_exit("NEW RETURN TYPE!")


def fix_bracket(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing bracket errors")
    line_number = int(source_location.split(":")[1])

    original_statement = ""
    new_statement = "\n"
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def fix_argument_errors(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing argument errors")
    line_number = int(source_location.split(":")[1])
    ast_map = ast_generator.get_ast_json(source_file)
    function_node = finder.search_function_node_by_loc(ast_map, int(line_number), source_file)
    goto_node = extract_goto_node(function_node, line_number)
    function_definition = function_node['value']
    function_name = function_node['identifier']
    function_return_type = (function_definition.replace(function_name, "")).split("(")[1]
    start_line = goto_node['start line']
    end_line = goto_node['end line']
    original_statement = ""
    if function_return_type.strip() == "void":
        new_statement = "return;\n"
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, start_line)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)
    elif function_return_type.strip() == "int":
        new_statement = "return -1;\n"
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, start_line)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)
    else:
        error_exit("NEW RETURN TYPE!")


def fix_syntax_errors(source_file):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing syntax errors")
    with open(FILE_SYNTAX_ERRORS, 'r') as error_log:
        read_line_list = error_log.readlines()
        for read_line in read_line_list:
            if ": " not in read_line:
                continue
            if " error:" not in read_line:
                continue
            source_location = read_line.split(": ")[0]
            if ".h" in source_location:
                continue
            error_type = (read_line.split(" [")[-1]).replace("]", "")
            if "return-type" in error_type:
                fix_return_type(source_file, source_location)
            elif "use of undeclared label" in read_line:
                fix_label_error(source_file, source_location)
            elif "too many arguments provided" in read_line:
                fix_argument_errors(source_file, source_location)
            elif "extraneous closing brace" in read_line:
                fix_bracket(source_file, source_location)
            elif "redefinition of" in read_line:
                fix_redeclaration_error(source_file, source_location)
            elif "expected ';'" in read_line:
                fix_semicolon_error(source_file, source_location)
            elif "implicit declaration of function" in read_line:
                fix_unknown_function_calls(source_file, source_location)
            elif "extraneous ')' before ';'" in read_line:
                fix_paranthese_error(source_file, source_location, True)
            elif "expected ')'" in read_line:
                fix_paranthese_error(source_file, source_location)
            elif "expected expression before ',' token" in read_line:
                fix_comma_error(source_file, source_location)
            elif "error: expected expression" in read_line:
                fix_initialization_error(source_file, source_location)
            elif "error: member reference" in read_line:
                fix_pointer_error(source_file, source_location, False)


def fix_initialization_error(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing initialization errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    if ";=" in original_statement:
        new_statement = original_statement.replace(";=", "=")
    elif ", ," in original_statement:
        new_statement = original_statement.replace(", ,", ",")
    if new_statement:
        emitter.information("replaced statement: " + new_statement)
        backup_file(source_file, FILENAME_BACKUP)
        replace_code(new_statement, source_file, line_number)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_file)


def fix_unknown_function_calls(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing semicolon errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    new_statement = "\n"
    emitter.information("replaced statement: " + new_statement)
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def fix_redeclaration_error(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing redeclaration errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    new_statement = original_statement.split(";")[1] + ";\n"
    emitter.information("replaced statement: " + new_statement)
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def fix_comma_error(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing comma errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    new_statement = original_statement.replace(", ,", ",")
    emitter.information("replaced statement: " + new_statement)
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def fix_semicolon_error(source_file, source_location):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing semicolon errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    new_statement = original_statement.replace("\n", ";\n")
    emitter.information("replaced statement: " + new_statement)
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def fix_paranthese_error(source_file, source_location, remove=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing paranthese errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    if remove:
        new_statement = original_statement.replace(");", ";")
    else:
        new_statement = original_statement.replace(";", ");")
    emitter.information("replaced statement: " + new_statement)
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def fix_pointer_error(source_file, source_location, remove=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfixing pointer errors")
    line_number = int(source_location.split(":")[1])
    emitter.information("fetching line number: " + str(line_number))
    original_statement = get_code(source_file, line_number)
    emitter.information("replacing statement: " + original_statement)
    new_statement = original_statement.replace("->", ".", 1)
    emitter.information("replaced statement: " + new_statement)
    backup_file(source_file, FILENAME_BACKUP)
    replace_code(new_statement, source_file, line_number)
    backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    show_partial_diff(backup_file_path, source_file)


def check_syntax_errors(modified_source_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.sub_sub_title("computing syntax errors")
    for source_file in modified_source_list:
        emitter.normal("\t" + source_file)
        if source_file[-1] == "h":
            emitter.normal("\t\tskipping header file")
            continue
        emitter.normal("\t\tchecking syntax errors")
        check_command = "clang-check -analyze " + source_file + " > " + FILE_SYNTAX_ERRORS
        check_command += " 2>&1"
        ret_code = int(execute_command(check_command))
        if ret_code != 0:
            fix_syntax_errors(source_file)
        else:
            emitter.normal("\t\tno syntax errors")


def set_values():
    global FILE_SYNTAX_ERRORS
    FILE_SYNTAX_ERRORS = definitions.DIRECTORY_OUTPUT + "/syntax-errors"


def check(modified_source_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    set_values()
    check_syntax_errors(modified_source_list)
