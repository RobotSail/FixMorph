#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printA(int a, char* str){
    printf("A: the values are  %d %s\n", a, str);
}

void printB(int a, char* str){
    printf("B: the values are  %d %s\n", a, str);
}



int main( ) {
    int i = 2;
    printA(i, "printA");
    printB(i, "printB");
    return 0;
}
