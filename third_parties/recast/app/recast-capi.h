/*
 *
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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 * This file was forked from Blender 2.79b.
 *
 * Contributor(s): Sergey Sharybin,
 *                 Przemysław Bągard,
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef RECAST_C_API_H
#define RECAST_C_API_H

// for size_t
#include <stddef.h>
#include "recast-capi_global.h"

#ifdef __cplusplus
extern "C" {
#endif

struct RECASTBLENDERADDON_EXPORT recast_polyMesh;
struct RECASTBLENDERADDON_EXPORT recast_polyMeshDetail;
struct RECASTBLENDERADDON_EXPORT recast_heightfield;
struct RECASTBLENDERADDON_EXPORT recast_compactHeightfield;
struct RECASTBLENDERADDON_EXPORT recast_heightfieldLayerSet;
struct RECASTBLENDERADDON_EXPORT recast_contourSet;

// recast_polyMesh must match rcPolyMesh
///// Represents a polygon mesh suitable for use in building a navigation mesh.
///// @ingroup recast
//struct rcPolyMesh
//{
//	rcPolyMesh();
//	~rcPolyMesh();
//	unsigned short* verts;	///< The mesh vertices. [Form: (x, y, z) * #nverts]
//	unsigned short* polys;	///< Polygon and neighbor data. [Length: #maxpolys * 2 * #nvp]
//	unsigned short* regs;	///< The region id assigned to each polygon. [Length: #maxpolys]
//	unsigned short* flags;	///< The user defined flags for each polygon. [Length: #maxpolys]
//	unsigned char* areas;	///< The area id assigned to each polygon. [Length: #maxpolys]
//	int nverts;				///< The number of vertices.
//	int npolys;				///< The number of polygons.
//	int maxpolys;			///< The number of allocated polygons.
//	int nvp;				///< The maximum number of vertices per polygon.
//	float bmin[3];			///< The minimum bounds in world space. [(x, y, z)]
//	float bmax[3];			///< The maximum bounds in world space. [(x, y, z)]
//	float cs;				///< The size of each cell. (On the xz-plane.)
//	float ch;				///< The height of each cell. (The minimum increment along the y-axis.)
//	int borderSize;			///< The AABB border size used to generate the source data from which the mesh was derived.
//	float maxEdgeError;		///< The max error of the polygon edges in the mesh.
//};

///// Contains triangle meshes that represent detailed height data associated
///// with the polygons in its associated polygon mesh object.
///// @ingroup recast
//struct rcPolyMeshDetail
//{
//	unsigned int* meshes;	///< The sub-mesh data. [Size: 4*#nmeshes]
//	float* verts;			///< The mesh vertices. [Size: 3*#nverts]
//	unsigned char* tris;	///< The mesh triangles. [Size: 4*#ntris]
//	int nmeshes;			///< The number of sub-meshes defined by #meshes.
//	int nverts;				///< The number of vertices in #verts.
//	int ntris;				///< The number of triangles in #tris.
//};



enum RECASTBLENDERADDON_EXPORT recast_BuildContoursFlags
{
	RECAST_CONTOUR_TESS_WALL_EDGES = 0x01,
	RECAST_CONTOUR_TESS_AREA_EDGES = 0x02,
};

//int recast_buildMeshAdjacency(unsigned short* polys, const int npolys,
//			const int nverts, const int vertsPerPoly);

RECASTBLENDERADDON_EXPORT void recast_calcBounds(const float *verts, int nv, float *bmin, float *bmax);

RECASTBLENDERADDON_EXPORT void recast_calcGridSize(const float *bmin, const float *bmax, float cs, int *w, int *h);

RECASTBLENDERADDON_EXPORT struct recast_heightfield *recast_newHeightfield(void);

RECASTBLENDERADDON_EXPORT void recast_destroyHeightfield(struct recast_heightfield *heightfield);

RECASTBLENDERADDON_EXPORT int recast_createHeightfield(struct recast_heightfield *hf, int width, int height,
			const float *bmin, const float* bmax, float cs, float ch);

RECASTBLENDERADDON_EXPORT void recast_markWalkableTriangles(const float walkableSlopeAngle,const float *verts, int nv,
			const int *tris, int nt, unsigned char *areas);

RECASTBLENDERADDON_EXPORT void recast_clearUnwalkableTriangles(const float walkableSlopeAngle, const float* verts, int nv,
			const int* tris, int nt, unsigned char* areas);

RECASTBLENDERADDON_EXPORT int recast_addSpan(struct recast_heightfield *hf, const int x, const int y,
			const unsigned short smin, const unsigned short smax,
			const unsigned char area, const int flagMergeThr);

RECASTBLENDERADDON_EXPORT int recast_rasterizeTriangle(const float* v0, const float* v1, const float* v2,
			const unsigned char area, struct recast_heightfield *solid,
			const int flagMergeThr);

RECASTBLENDERADDON_EXPORT int recast_rasterizeTriangles(const float *verts, const int nv, const int *tris,
			const unsigned char *areas, const int nt, struct recast_heightfield *solid,
			const int flagMergeThr);

RECASTBLENDERADDON_EXPORT void recast_filterLedgeSpans(const int walkableHeight, const int walkableClimb,
			struct recast_heightfield *solid);

RECASTBLENDERADDON_EXPORT void recast_filterWalkableLowHeightSpans(int walkableHeight, struct recast_heightfield *solid);

RECASTBLENDERADDON_EXPORT void recast_filterLowHangingWalkableObstacles(const int walkableClimb, struct recast_heightfield *solid);

RECASTBLENDERADDON_EXPORT int recast_getHeightFieldSpanCount(struct recast_heightfield *hf);

RECASTBLENDERADDON_EXPORT struct recast_heightfieldLayerSet *recast_newHeightfieldLayerSet(void);

RECASTBLENDERADDON_EXPORT void recast_destroyHeightfieldLayerSet(struct recast_heightfieldLayerSet *lset);

RECASTBLENDERADDON_EXPORT struct recast_compactHeightfield *recast_newCompactHeightfield(void);

RECASTBLENDERADDON_EXPORT void recast_destroyCompactHeightfield(struct recast_compactHeightfield *compactHeightfield);

RECASTBLENDERADDON_EXPORT int recast_buildCompactHeightfield(const int walkableHeight, const int walkableClimb,
			struct recast_heightfield *hf, struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT int recast_erodeWalkableArea(int radius, struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT int recast_medianFilterWalkableArea(struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT void recast_markBoxArea(const float *bmin, const float *bmax, unsigned char areaId,
			struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT void recast_markConvexPolyArea(const float* verts, const int nverts,
			const float hmin, const float hmax, unsigned char areaId,
			struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT int recast_offsetPoly(const float* verts, const int nverts,
			const float offset, float *outVerts, const int maxOutVerts);

RECASTBLENDERADDON_EXPORT void recast_markCylinderArea(const float* pos, const float r, const float h,
			unsigned char areaId, struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT int recast_buildDistanceField(struct recast_compactHeightfield *chf);

RECASTBLENDERADDON_EXPORT int recast_buildRegions(struct recast_compactHeightfield *chf,
			const int borderSize, const int minRegionArea, const int mergeRegionArea);

RECASTBLENDERADDON_EXPORT int recast_buildLayerRegions(struct recast_compactHeightfield *chf,
			const int borderSize, const int minRegionArea);

RECASTBLENDERADDON_EXPORT int recast_buildRegionsMonotone(struct recast_compactHeightfield *chf,
			const int borderSize, const int minRegionArea, const int mergeRegionArea);

/* Contour set */

RECASTBLENDERADDON_EXPORT struct recast_contourSet *recast_newContourSet(void);

RECASTBLENDERADDON_EXPORT void recast_destroyContourSet(struct recast_contourSet *contourSet);

RECASTBLENDERADDON_EXPORT int recast_buildContours(struct recast_compactHeightfield *chf,
			const float maxError, const int maxEdgeLen, struct recast_contourSet *cset,
			const int buildFlags);

/* Poly mesh */

RECASTBLENDERADDON_EXPORT struct recast_polyMesh *recast_newPolyMesh(void);

RECASTBLENDERADDON_EXPORT void recast_destroyPolyMesh(struct recast_polyMesh *polyMesh);

RECASTBLENDERADDON_EXPORT int recast_buildPolyMesh(struct recast_contourSet *cset, const int nvp, struct recast_polyMesh *mesh);

RECASTBLENDERADDON_EXPORT int recast_mergePolyMeshes(struct recast_polyMesh **meshes, const int nmeshes, struct recast_polyMesh *mesh);

RECASTBLENDERADDON_EXPORT int recast_copyPolyMesh(const struct recast_polyMesh *src, struct recast_polyMesh *dst);

RECASTBLENDERADDON_EXPORT unsigned short *recast_polyMeshGetVerts(struct recast_polyMesh *mesh, int *nverts);

RECASTBLENDERADDON_EXPORT void recast_polyMeshGetBoundbox(struct recast_polyMesh *mesh, float *bmin, float *bmax);

RECASTBLENDERADDON_EXPORT void recast_polyMeshGetCell(struct recast_polyMesh *mesh, float *cs, float *ch);

RECASTBLENDERADDON_EXPORT unsigned short *recast_polyMeshGetPolys(struct recast_polyMesh *mesh, int *npolys, int *nvp);

/* Poly mesh detail */

RECASTBLENDERADDON_EXPORT struct recast_polyMeshDetail *recast_newPolyMeshDetail(void);

RECASTBLENDERADDON_EXPORT void recast_destroyPolyMeshDetail(struct recast_polyMeshDetail *polyMeshDetail);

RECASTBLENDERADDON_EXPORT int recast_buildPolyMeshDetail(const struct recast_polyMesh *mesh, const struct recast_compactHeightfield *chf,
			const float sampleDist, const float sampleMaxError, struct recast_polyMeshDetail *dmesh);

RECASTBLENDERADDON_EXPORT int recast_mergePolyMeshDetails(struct recast_polyMeshDetail **meshes, const int nmeshes, struct recast_polyMeshDetail *mesh);

RECASTBLENDERADDON_EXPORT float *recast_polyMeshDetailGetVerts(struct recast_polyMeshDetail *mesh, int *nverts);

RECASTBLENDERADDON_EXPORT unsigned char *recast_polyMeshDetailGetTris(struct recast_polyMeshDetail *mesh, int *ntris);

RECASTBLENDERADDON_EXPORT unsigned int *recast_polyMeshDetailGetMeshes(struct recast_polyMeshDetail *mesh, int *nmeshes);

#ifdef __cplusplus
}
#endif

#endif // RECAST_C_API_H
