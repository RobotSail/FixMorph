import time
from common import Definitions, Values
from common.Utilities import execute_command, error_exit
from tools import Emitter

file_index = 1
backup_file_list = dict()


def apply_patch(file_a, file_b, file_c, instruction_list):
    # Check for an edit script
    script_file_name = "output/" + str(file_index) + "_script"
    syntax_error_file_name = "output/" + str(file_index) + "_syntax_errors"
    with open(script_file_name, 'w') as script_file:
        for instruction in instruction_list:
            script_file.write(instruction + "\n")

    output_file = "output/" + str(file_index) + "_temp." + file_c[-1]
    c = ""
    # We add file_c into our dict (changes) to be able to backup and copy it
    if file_c not in backup_file_list.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(file_index) + "_" + filename
        backup_file_list[file_c] = backup_file
        c += "cp " + file_c + " backup/" + backup_file + "; "

    # We apply the patch using the script and crochet-patch
    c += Definitions.PATCH_COMMAND + " -s=" + Definitions.PATCH_SIZE + \
         " -script=" + script_file_name + " -source=" + file_a + \
         " -destination=" + file_b + " -target=" + file_c
    if file_c[-1] == "h":
        c += " --"
    c += " 2> output/errors > " + output_file + "; "
    c += "cp " + output_file + " " + file_c
    #Print.grey(c)
    execute_command(c)
    # We fix basic syntax errors that could have been introduced by the patch
    c2 = Definitions.SYNTAX_CHECK_COMMAND + "-fixit " + file_c
    if file_c[-1] == "h":
        c2 += " --"
    c2 += " 2>" + syntax_error_file_name
    execute_command(c2)
    # We check that everything went fine, otherwise, we restore everything
    try:
        c3 = Definitions.SYNTAX_CHECK_COMMAND + file_c + " 2>" + syntax_error_file_name
        if file_c[-1] == "h":
            c3 += " --"
        execute_command(c3)
    except Exception as e:
        Emitter.error("Clang-check could not repair syntax errors.")
        restore_files()
        error_exit(e, "Crochet failed.")
    # We format the file to be with proper spacing (needed?)
    c4 = Definitions.STYLE_FORMAT_COMMAND + file_c
    if file_c[-1] == "h":
        c4 += " --"
    c4 += " > " + output_file + "; "
    execute_command(c4)
    show_patch(file_a, file_b, "backup/" + backup_file, output_file, str(file_index))
    c5 = "cp " + output_file + " " + file_c + ";"
    execute_command(c5)
    Emitter.success("\n\tSuccessful transformation")


def restore_files():
    global backup_file_list
    Emitter.warning("Restoring files...")
    for file in backup_file_list.keys():
        backup_file = backup_file_list[file]
        c = "cp backup/" + backup_file + " " + file
        execute_command(c)
    Emitter.warning("Files restored")


def show_patch(file_a, file_b, file_c, file_d, index):
    Emitter.special("Original Patch")
    original_patch_file_name = "output/" + index + "-original-patch"
    generated_patch_file_name = "output/" + index + "-generated-patch"
    diff_command = "diff -ENZBbwr " + file_a + " " + file_b + " > " + original_patch_file_name
    execute_command(diff_command)
    with open(original_patch_file_name, 'r') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Emitter.special("\t" + diff_line)
            diff_line = diff.readline().strip()

    Emitter.special("Generated Patch")
    diff_command = "diff -ENZBbwr " + file_c + " " + file_d + " > " + generated_patch_file_name
    execute_command(diff_command)
    with open(generated_patch_file_name, 'r') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Emitter.information("\t" + diff_line)
            diff_line = diff.readline().strip()


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Emitter.error("Crash during " + description + ", after " + duration + " seconds.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def weave():
    global file_index
    Emitter.title("Applying transformation")
    for file_list, generated_data in Values.translated_script_for_files.items():
        Emitter.sub_title("Transforming file " + file_list[2])
        Emitter.special("Original AST script")
        original_script = generated_data[1]
        Emitter.emit_ast_script(original_script)
        Emitter.special("Generated AST script")
        translated_script = generated_data[0]
        Emitter.emit_ast_script(translated_script)
        apply_patch(file_list[0], file_list[1], file_list[2], translated_script)
        file_index += 1
