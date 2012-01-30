// perfect.c
// Tests if a number is a perfect number (equal to the sum of its divisors)
//

#include <stdlib.h>
#include <stdio.h>
#include "divisor.h"

int is_perfect(int n) {
  int i;
  int sum = 0;
  
  int* ds = divisors(n);
  int len = ds[0];
  
  for (i = 1; i <= len; i++) {
    sum += ds[i];
  }
  return sum == n;
}

int main(int argc, char **argv) {
  int num, i;
  if(argc > 1) {
    num = atoi(argv[1]);
    
    for (i = 1; i <= num; i++) {
      if(is_perfect(i)) {
        printf("%d is perfect\n", i);
      }
    }
  }

  exit(0);
}

