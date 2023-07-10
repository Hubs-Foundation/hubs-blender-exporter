/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2011 by Blender Foundation
 * All rights reserved.
 *
 * Contributor(s): Benoit Bolsee,
 *                 Nick Samarin,
 *                 Przemysław Bągard,
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef MESH_NAVMESH_H
#define MESH_NAVMESH_H

#include "recast-capi.h"

#ifdef __cplusplus
extern "C" {
#endif

/// Just holder class which will allocate pmesh inside.
/// This class will be created on python side.
struct RECASTBLENDERADDON_EXPORT recast_polyMesh_holder
{
    struct recast_polyMesh *pmesh;
};

struct RECASTBLENDERADDON_EXPORT recast_polyMeshDetail_holder
{
    struct recast_polyMeshDetail *dmesh;
};

typedef RECASTBLENDERADDON_EXPORT struct RecastData {
    float cellsize;
    float cellheight;
    float agentmaxslope;
    float agentmaxclimb;
    float agentheight;
    float agentradius;
    float edgemaxlen;
    float edgemaxerror;
    float regionminsize;
    float regionmergesize;
    int vertsperpoly;
    float detailsampledist;
    float detailsamplemaxerror;
//    short pad1, pad2;
    short partitioning;
    short pad1;
} RecastData;

/* RecastData.partitioning */
#define RC_PARTITION_WATERSHED 0
#define RC_PARTITION_MONOTONE 1
#define RC_PARTITION_LAYERS 2

//#if (defined(__GNUC__) && ((__GNUC__ * 100 + __GNUC_MINOR__) >= 403))
//#  define ATTR_MALLOC __attribute__((malloc))
//#else
//#  define ATTR_MALLOC
//#endif

//void MEM_lockfree_freeN(void *vmemh);
//void *MEM_lockfree_callocN(size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);

//void (*MEM_freeN)(void *vmemh) = MEM_lockfree_freeN;
//void *(*MEM_callocN)(size_t len, const char *str) = MEM_lockfree_callocN;


int RECASTBLENDERADDON_EXPORT buildNavMesh(const RecastData *recastParams, int nverts, float *verts, int ntris, int *tris,
                                                     struct recast_polyMesh_holder *pmeshHolder, struct recast_polyMeshDetail_holder *dmeshHolder,
                                                     char *reports, int reportsMaxChars);


int RECASTBLENDERADDON_EXPORT freeNavMesh(struct recast_polyMesh_holder *pmeshHolder, struct recast_polyMeshDetail_holder *dmeshHolder,
                                                    char *reports, int reportsMaxChars);



#ifdef __cplusplus
}
#endif

#endif
