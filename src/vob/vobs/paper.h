#ifndef VOB_VOBS_PAPER_H
#define VOB_VOBS_PAPER_H

#include "vob/api.h"
#include "vob/scene.h"

struct vob_paper {
	Vob base;
	unsigned long id;
};
typedef struct vob_paper Paper;

Vob1 *vob_paper(Scene *vs, unsigned long id);


#endif
