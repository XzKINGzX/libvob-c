// (c): Matti J. Katila


#ifndef UTIL_ARRAY_H
#define UTIL_ARRAY_H

#include "util/regions.h"

struct util_array {
	int size;
	int capacity;
	void **data;
};
typedef struct util_array UtilArray;


UtilArray *util_arr_create(Region *reg);


void util_arr_add(Region *reg, UtilArray *arr, void *data);

/**
 * for (int i=0; i<arr->size; i++) {
 *     char *str = util_arr_get(i);
 * }
 */
void *util_arr_get(UtilArray *arr, int idx);
void util_arr_set(UtilArray *arr, int idx, void *data);

char *util_arr_get_str(UtilArray *arr, int idx);


#endif
