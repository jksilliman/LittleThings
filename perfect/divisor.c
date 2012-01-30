// divisor.c
// returns an array of factors of an integer

#include <stdio.h>
#include "divisor.h"
#include "list.h"

LinkedList* divisor_list(int n);

int* divisors(int n) {
  LinkedList *list = divisor_list(n);
  int *array = list_to_array(list);
  destroy_list(list);
  return array;
}

LinkedList* divisor_list(int n) {
  LinkedList* l = new_list();
  int i;
  for (i = 1; i < n; i++) {
    if(n%i == 0) {
      l = append(l,i);
    }
  }
  return l;
}
