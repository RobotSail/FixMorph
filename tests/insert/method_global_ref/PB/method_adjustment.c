#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testFunc(int a, char* str){
    printf("the value of a is %d %s\n", a, str);
}

int main( ) {
    testFunc(1, "test"); 
    return 0;
}