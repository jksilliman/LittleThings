// list.c
// A simple linked-list. 

#include <stdlib.h>
#include "list.h"

LinkedList* new_list() {
  LinkedList* l = malloc(sizeof(LinkedList));
  l->next = NULL;
  l->data = 0;
  return l;
}

void destroy_list(LinkedList *lp) {
  destroy_list(lp->next);
  free((void *) lp);
}


LinkedList* append(LinkedList* l, int n) {
  LinkedList* next = new_list();
  next->data = n;
  next->next = l;
  return next;
}

int length(LinkedList* l) {
  int i = 0;
  LinkedList* current = l;
  while ( current->next != NULL ) {
    current = current->next; 
    i++;
  }

  return i;
}

int* list_to_array(LinkedList* l) {
  int *arr;
  int len = length(l);

  arr = (int *) malloc(length(l) * (sizeof(int)+1));
  LinkedList* current = l;
  
  arr[0] = len;
  int i = 1;
  while ( current->next != NULL ) {
    arr[i] = current->data;
    current = current->next;
    i++;
  }
  return arr;
}

