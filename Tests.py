# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:30:48 2018

@author: pedrobw
"""

import time
import Project
import ASTgen
import ASTVector
import gumtreeASTparser
import Print

examples_path = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/"

def test_ASTparsing():
    path = examples_path + "Backporting/Buffer_Overflow-Espruino/Pc/"
    project = Project.Project(path, "P")
    path_to_file = "targets/esp8266/esp8266_board_utils.c"
    file = path + path_to_file
    ASTgen.parseAST(file, project)
    
def test_ASTparsing1():
    src = examples_path + "Backporting/Null_Pointer_Dereference-Binutils/Pc/"
    project = Project.Project(src, "P")
    file = src + "bfd/pc532-mach.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.parseAST(file, project)
    
    
def test_gumtreeParsing1():
    for i in gumtreeASTparser.AST_from_file("gumtree_parse_test"):
        Print.white(i)
    
    
def test_gumtreeParsing2():
    l = gumtreeASTparser.AST_from_file("gumtree_parse_test")
    root = l[-1]
    gumtreeASTparser.recursive_print(root)
    
def test_gen_AST():
    src = examples_path + "Backporting/Invalid_Memory_Read-GraphicsMagick/Pc/"
    file = src + "hp2xx/old/to_pcx.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    file = src + "ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    
def test_gen_AST1():
    src = examples_path + "Backporting/Null_Pointer_Dereference-Binutils/Pc/"
    file = src + "bfd/pc532-mach.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    
def test_dist():
    file1 = examples_path + "Backporting/Buffer_Overflow-Jasper-2/Pa/" + \
            "src/libjasper/jpc/jpc_dec.c.jpc_dec_process_siz.vec"
    file2 = examples_path + "Backporting/Buffer_Overflow-Jasper-2/Pc/" + \
            "src/libjasper/jpc/jpc_dec.c.jpc_dec_process_siz.vec"
    file3 = examples_path + "Backporting/Buffer_Overflow-Jasper-2/Pc/" + \
            "src/libjasper/jpc/jpc_dec.c.jpc_dec_process_cod.vec"
    
    Print.white("Absolute distance:")    
    d12 = ASTVector.ASTVector.file_dist(file1, file2)
    d13 = ASTVector.ASTVector.file_dist(file1, file3)
    Print.white(str(d12) + " < " + str(d13) + " ? " + str(d12 < d13))
    d12 = ASTVector.ASTVector.file_dist(file1, file2, normed=False)
    d13 = ASTVector.ASTVector.file_dist(file1, file3, normed=False)
    Print.white("Relative distance:")
    Print.white(str(d12) + " < " + str(d13) + " ? " + str(d12 < d13))
    
def test_function_gen():
    fileA = examples_path + "Backporting/Buffer_Overflow-Espruino/Pa/src"
    fileB = examples_path + "Backporting/Buffer_Overflow-Espruino/Pa/src"
    
def run():
    Print.title("Running crochet tests...")
    tests = [
             #test_ASTparsing,
             test_ASTparsing1,
             #test_gumtreeParsing1,
             #test_gumtreeParsing2,
             #test_gen_AST,
             #test_gen_AST1,
             test_dist
             ]
    for i in tests:
        Print.green("-"*120)
        Print.rose("Starting test " + str(i.__name__) + "...")
        print("")
        start = time.time()
        i()
        end = time.time()
        secs = str(end - start)
        print("")
        Print.rose("Successful test after " + secs + " seconds.")
        print("")
    Print.green("-"*150)
    

if __name__=="__main__":
    run()