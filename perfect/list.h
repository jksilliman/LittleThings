// list.h
#ifndef LIST_H
#define LIST_H

struct LinkedList;
typedef struct LinkedList LinkedList;
struct LinkedList {
  int data;
  LinkedList *next;
};

LinkedList* new_list();
void destroy_list(LinkedList *lp);
LinkedList* append(LinkedList *lp, int n);
int length(LinkedList *lp);
int* list_to_array(LinkedList *lp);

#endif
