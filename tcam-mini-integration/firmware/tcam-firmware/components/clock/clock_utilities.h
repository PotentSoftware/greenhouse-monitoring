#ifndef CLOCK_UTILITIES_H
#define CLOCK_UTILITIES_H

#include <sys/time.h>

#ifdef __cplusplus
extern "C" {
#endif

// Time management functions
void time_init(void);
void time_set(struct timeval* tv);
void time_get(struct timeval* tv);

#ifdef __cplusplus
}
#endif

#endif // CLOCK_UTILITIES_H
