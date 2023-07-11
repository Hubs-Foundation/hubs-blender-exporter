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
 * This file was forked from Blender 2.79b.
 *
 * Contributor(s): Benoit Bolsee,
 *                 Nick Samarin,
 *                 Przemysław Bągard,
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mesh/mesh_navmesh.c
 *  \ingroup edmesh
 */

#define _USE_MATH_DEFINES
#include <cmath>
#include "math.h"
#include <Recast.h>
#include <stdio.h>
#include <string.h>
#include "mesh_navmesh.h"
#include "recast-capi.h"

#define RAD2DEGF(_rad) ((_rad)*(float)(180.0/M_PI))
#define DEG2RADF(_deg) ((_deg)*(float)(M_PI/180.0))

int buildNavMesh(const RecastData *recastParams, int nverts, float *verts, int ntris, int *tris,
                 struct recast_polyMesh_holder *pmeshHolder, struct recast_polyMeshDetail_holder *dmeshHolder,
                 char *reports, int reportsMaxChars)
{
    float bmin[3], bmax[3];
    struct recast_heightfield *solid;
    unsigned char *triflags;
    struct recast_compactHeightfield *chf;
    struct recast_contourSet *cset;
    int width, height, walkableHeight, walkableClimb, walkableRadius;
    int minRegionArea, mergeRegionArea, maxEdgeLen;
    float detailSampleDist, detailSampleMaxError;

    printf("--- buildNavMesh start params\n");
    printf("Cell size: %f\n", recastParams->cellsize);
    printf("nverts: %i\n", nverts);
    printf("ntris: %i\n", ntris);
    printf("reportsMaxChars: %i\n", reportsMaxChars);
#ifdef VERBOSE_LOGS
    for (int i = 0; i < nverts; ++i) {
        printf("verts[%i]: (%f, %f, %f)\n", i, verts[i*3+0], verts[i*3+1], verts[i*3+2]);
    }
    for (int i = 0; i < ntris; ++i) {
        printf("tris[%i]: (%i, %i, %i)\n", i, tris[i*3+0], tris[i*3+1], tris[i*3+2]);
    }
#endif
    printf("buildNavMesh start params ---\n");


    /* clear reports string */
    strncpy(reports, "", reportsMaxChars);
    pmeshHolder->pmesh = NULL;
    dmeshHolder->dmesh = NULL;

    recast_calcBounds(verts, nverts, bmin, bmax);

    /* ** Step 1. Initialize build config ** */
    walkableHeight = (int)ceilf(recastParams->agentheight / recastParams->cellheight);
    walkableClimb = (int)floorf(recastParams->agentmaxclimb / recastParams->cellheight);
    walkableRadius = (int)ceilf(recastParams->agentradius / recastParams->cellsize);
    minRegionArea = (int)(recastParams->regionminsize * recastParams->regionminsize);
    mergeRegionArea = (int)(recastParams->regionmergesize * recastParams->regionmergesize);
    maxEdgeLen = (int)(recastParams->edgemaxlen / recastParams->cellsize);
    detailSampleDist = recastParams->detailsampledist < 0.9f ? 0 :
                       recastParams->cellsize * recastParams->detailsampledist;
    detailSampleMaxError = recastParams->cellheight * recastParams->detailsamplemaxerror;

    /* Set the area where the navigation will be build. */
    recast_calcGridSize(bmin, bmax, recastParams->cellsize, &width, &height);

    /* zero dimensions cause zero alloc later on [#33758] */
    if (width <= 0 || height <= 0) {
        strncpy(reports, "Object has a width or height of zero", reportsMaxChars);
        return 0;
    }

    /* ** Step 2: Rasterize input polygon soup ** */
    /* Allocate voxel heightfield where we rasterize our input data to */
    solid = recast_newHeightfield();

    if (!recast_createHeightfield(solid, width, height, bmin, bmax, recastParams->cellsize, recastParams->cellheight)) {
        recast_destroyHeightfield(solid);
        strncpy(reports, "Failed to create height field", reportsMaxChars);
        return 0;
    }

    /* Allocate array that can hold triangle flags */
//    triflags = MEM_callocN(sizeof(unsigned char) * ntris, "buildNavMesh triflags");
//    triflags = (unsigned char *)calloc(ntris, sizeof(unsigned char));
    triflags = new unsigned char[ntris];
    memset(triflags, 0, ntris*sizeof(unsigned char));

    /* Find triangles which are walkable based on their slope and rasterize them */
    recast_markWalkableTriangles(RAD2DEGF(recastParams->agentmaxslope), verts, nverts, tris, ntris, triflags);
    recast_rasterizeTriangles(verts, nverts, tris, triflags, ntris, solid, 1);
//    MEM_freeN(triflags);
//    free(triflags);
    delete [] triflags;


    /* ** Step 3: Filter walkables surfaces ** */
    recast_filterLowHangingWalkableObstacles(walkableClimb, solid);
    recast_filterLedgeSpans(walkableHeight, walkableClimb, solid);
    recast_filterWalkableLowHeightSpans(walkableHeight, solid);

    /* ** Step 4: Partition walkable surface to simple regions ** */

    chf = recast_newCompactHeightfield();
    if (!recast_buildCompactHeightfield(walkableHeight, walkableClimb, solid, chf)) {
        recast_destroyHeightfield(solid);
        recast_destroyCompactHeightfield(chf);

        strncpy(reports, "Failed to create compact height field", reportsMaxChars);
        return 0;
    }

    recast_destroyHeightfield(solid);
    solid = NULL;

    if (!recast_erodeWalkableArea(walkableRadius, chf)) {
        recast_destroyCompactHeightfield(chf);

        strncpy(reports, "Failed to erode walkable area", reportsMaxChars);
        return 0;
    }

    if (recastParams->partitioning == RC_PARTITION_WATERSHED) {
        /* Prepare for region partitioning, by calculating distance field along the walkable surface */
        if (!recast_buildDistanceField(chf)) {
            recast_destroyCompactHeightfield(chf);

            strncpy(reports, "Failed to build distance field", reportsMaxChars);
            return 0;
        }

        /* Partition the walkable surface into simple regions without holes */
        if (!recast_buildRegions(chf, 0, minRegionArea, mergeRegionArea)) {
            recast_destroyCompactHeightfield(chf);

            strncpy(reports, "Failed to build watershed regions", reportsMaxChars);
            return 0;
        }
    }
    else if (recastParams->partitioning == RC_PARTITION_MONOTONE) {
        /* Partition the walkable surface into simple regions without holes */
        /* Monotone partitioning does not need distancefield. */
        if (!recast_buildRegionsMonotone(chf, 0, minRegionArea, mergeRegionArea)) {
            recast_destroyCompactHeightfield(chf);

            strncpy(reports, "Failed to build monotone regions", reportsMaxChars);
            return 0;
        }
    }
    else { /* RC_PARTITION_LAYERS */
        /* Partition the walkable surface into simple regions without holes */
        if (!recast_buildLayerRegions(chf, 0, minRegionArea)) {
            recast_destroyCompactHeightfield(chf);

            strncpy(reports, "Failed to build layer regions", reportsMaxChars);
            return 0;
        }
    }

    /* ** Step 5: Trace and simplify region contours ** */
    /* Create contours */
    cset = recast_newContourSet();

    if (!recast_buildContours(chf, recastParams->edgemaxerror, maxEdgeLen, cset, RECAST_CONTOUR_TESS_WALL_EDGES)) {
        recast_destroyCompactHeightfield(chf);
        recast_destroyContourSet(cset);

        strncpy(reports, "Failed to build contours", reportsMaxChars);
        return 0;
    }

    /* ** Step 6: Build polygons mesh from contours ** */
    pmeshHolder->pmesh = recast_newPolyMesh();
    if (!recast_buildPolyMesh(cset, recastParams->vertsperpoly, pmeshHolder->pmesh)) {
        recast_destroyCompactHeightfield(chf);
        recast_destroyContourSet(cset);
        recast_destroyPolyMesh(pmeshHolder->pmesh);

        strncpy(reports, "Failed to build poly mesh", reportsMaxChars);
        return 0;
    }


    /* ** Step 7: Create detail mesh which allows to access approximate height on each polygon ** */

    dmeshHolder->dmesh = recast_newPolyMeshDetail();
    if (!recast_buildPolyMeshDetail(pmeshHolder->pmesh, chf, detailSampleDist, detailSampleMaxError, dmeshHolder->dmesh)) {
        recast_destroyCompactHeightfield(chf);
        recast_destroyContourSet(cset);
        recast_destroyPolyMesh(pmeshHolder->pmesh);
        recast_destroyPolyMeshDetail(dmeshHolder->dmesh);

        strncpy(reports, "Failed to build poly mesh detail", reportsMaxChars);
        return 0;
    }

    recast_destroyCompactHeightfield(chf);
    recast_destroyContourSet(cset);

    printf("--- buildNavMesh end params\n");
    if(pmeshHolder->pmesh) {
        printf("- pmesh:\n");
        struct rcPolyMesh* pmesh = (struct rcPolyMesh*)(pmeshHolder->pmesh);
        printf("pmesh->nverts: %i\n", pmesh->nverts);
        printf("pmesh->npolys: %i\n", pmesh->npolys);
        printf("pmesh->maxpolys: %i\n", pmesh->maxpolys);
        printf("pmesh->nvp: %i\n", pmesh->nvp);
        printf("pmesh->bmin: (%f, %f, %f)\n", pmesh->bmin[0], pmesh->bmin[1], pmesh->bmin[2]);
        printf("pmesh->bmax: (%f, %f, %f)\n", pmesh->bmax[0], pmesh->bmax[1], pmesh->bmax[2]);
        printf("pmesh->cs: %f\n", pmesh->cs);
        printf("pmesh->ch: %f\n", pmesh->ch);
        printf("pmesh->borderSize: %i\n", pmesh->borderSize);
        printf("pmesh->maxEdgeError: %f\n", pmesh->maxEdgeError);
#ifdef VERBOSE_LOGS
        for (int i = 0; i < pmesh->nverts; ++i) {
            printf("pmesh->verts[%i]: (%u, %u, %u)\n", i, pmesh->verts[i*3+0], pmesh->verts[i*3+1], pmesh->verts[i*3+2]);
        }
#endif
    }

    if(dmeshHolder->dmesh) {
        printf("- dmesh:\n");
        struct rcPolyMeshDetail* dmesh = (struct rcPolyMeshDetail*)(dmeshHolder->dmesh);
        printf("dmesh->nmeshes: %i\n", dmesh->nmeshes);
        printf("dmesh->nverts: %i\n", dmesh->nverts);
        printf("dmesh->ntris: %i\n", dmesh->ntris);
#ifdef VERBOSE_LOGS
        for (int i = 0; i < dmesh->nverts; ++i) {
            printf("dmesh->verts[%i]: (%f, %f, %f)\n", i, dmesh->verts[i*3+0], dmesh->verts[i*3+1], dmesh->verts[i*3+2]);
        }
        for (int i = 0; i < dmesh->ntris; ++i) {
            printf("dmesh->tris[%i]: (%u, %u, %u, %u)\n", i, dmesh->tris[i*4+0], dmesh->tris[i*4+1], dmesh->tris[i*4+2], dmesh->tris[i*4+3]);
        }
        for (int i = 0; i < dmesh->nmeshes; ++i) {
            printf("dmesh->meshes[%i]: (%u, %u, %u, %u)\n", i, dmesh->meshes[i*4+0], dmesh->meshes[i*4+1], dmesh->meshes[i*4+2], dmesh->meshes[i*4+3]);
        }
#endif
    }
    printf("buildNavMesh end params ---\n");

    return 1;
}

//int Sample_SoloMesh::handleBuild()
//{
//	if (!m_geom || !m_geom->getMesh())
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Input mesh is not specified.");
//		return 0;
//	}

//	cleanup();

//	const float* bmin = m_geom->getNavMeshBoundsMin();
//	const float* bmax = m_geom->getNavMeshBoundsMax();
//	const float* verts = m_geom->getMesh()->getVerts();
//	const int nverts = m_geom->getMesh()->getVertCount();
//	const int* tris = m_geom->getMesh()->getTris();
//	const int ntris = m_geom->getMesh()->getTriCount();

//	//
//	// Step 1. Initialize build config.
//	//

//	// Init build configuration from GUI
//	memset(&m_cfg, 0, sizeof(m_cfg));
//	m_cfg.cs = m_cellSize;
//	m_cfg.ch = m_cellHeight;
//	m_cfg.walkableSlopeAngle = m_agentMaxSlope;
//	m_cfg.walkableHeight = (int)ceilf(m_agentHeight / m_cfg.ch);
//	m_cfg.walkableClimb = (int)floorf(m_agentMaxClimb / m_cfg.ch);
//	m_cfg.walkableRadius = (int)ceilf(m_agentRadius / m_cfg.cs);
//	m_cfg.maxEdgeLen = (int)(m_edgeMaxLen / m_cellSize);
//	m_cfg.maxSimplificationError = m_edgeMaxError;
//	m_cfg.minRegionArea = (int)rcSqr(m_regionMinSize);		// Note: area = size*size
//	m_cfg.mergeRegionArea = (int)rcSqr(m_regionMergeSize);	// Note: area = size*size
//	m_cfg.maxVertsPerPoly = (int)m_vertsPerPoly;
//	m_cfg.detailSampleDist = m_detailSampleDist < 0.9f ? 0 : m_cellSize * m_detailSampleDist;
//	m_cfg.detailSampleMaxError = m_cellHeight * m_detailSampleMaxError;

//	// Set the area where the navigation will be build.
//	// Here the bounds of the input mesh are used, but the
//	// area could be specified by an user defined box, etc.
//	rcVcopy(m_cfg.bmin, bmin);
//	rcVcopy(m_cfg.bmax, bmax);
//	rcCalcGridSize(m_cfg.bmin, m_cfg.bmax, m_cfg.cs, &m_cfg.width, &m_cfg.height);

//	// Reset build times gathering.
//	m_ctx->resetTimers();

//	// Start the build process.
//	m_ctx->startTimer(RC_TIMER_TOTAL);

//	m_ctx->log(RC_LOG_PROGRESS, "Building navigation:");
//	m_ctx->log(RC_LOG_PROGRESS, " - %d x %d cells", m_cfg.width, m_cfg.height);
//	m_ctx->log(RC_LOG_PROGRESS, " - %.1fK verts, %.1fK tris", nverts/1000.0f, ntris/1000.0f);

//	//
//	// Step 2. Rasterize input polygon soup.
//	//

//	// Allocate voxel heightfield where we rasterize our input data to.
//	m_solid = rcAllocHeightfield();
//	if (!m_solid)
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Out of memory 'solid'.");
//		return 0;
//	}
//	if (!rcCreateHeightfield(m_ctx, *m_solid, m_cfg.width, m_cfg.height, m_cfg.bmin, m_cfg.bmax, m_cfg.cs, m_cfg.ch))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not create solid heightfield.");
//		return 0;
//	}

//	// Allocate array that can hold triangle area types.
//	// If you have multiple meshes you need to process, allocate
//	// and array which can hold the max number of triangles you need to process.
//	m_triareas = new unsigned char[ntris];
//	if (!m_triareas)
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Out of memory 'm_triareas' (%d).", ntris);
//		return 0;
//	}

//	// Find triangles which are walkable based on their slope and rasterize them.
//	// If your input data is multiple meshes, you can transform them here, calculate
//	// the are type for each of the meshes and rasterize them.
//	memset(m_triareas, 0, ntris*sizeof(unsigned char));
//	rcMarkWalkableTriangles(m_ctx, m_cfg.walkableSlopeAngle, verts, nverts, tris, ntris, m_triareas);
//	if (!rcRasterizeTriangles(m_ctx, verts, nverts, tris, m_triareas, ntris, *m_solid, m_cfg.walkableClimb))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not rasterize triangles.");
//		return 0;
//	}

//	if (!m_keepInterResults)
//	{
//		delete [] m_triareas;
//		m_triareas = 0;
//	}

//	//
//	// Step 3. Filter walkables surfaces.
//	//

//	// Once all geoemtry is rasterized, we do initial pass of filtering to
//	// remove unwanted overhangs caused by the conservative rasterization
//	// as well as filter spans where the character cannot possibly stand.
//	if (m_filterLowHangingObstacles)
//		rcFilterLowHangingWalkableObstacles(m_ctx, m_cfg.walkableClimb, *m_solid);
//	if (m_filterLedgeSpans)
//		rcFilterLedgeSpans(m_ctx, m_cfg.walkableHeight, m_cfg.walkableClimb, *m_solid);
//	if (m_filterWalkableLowHeightSpans)
//		rcFilterWalkableLowHeightSpans(m_ctx, m_cfg.walkableHeight, *m_solid);


//	//
//	// Step 4. Partition walkable surface to simple regions.
//	//

//	// Compact the heightfield so that it is faster to handle from now on.
//	// This will result more cache coherent data as well as the neighbours
//	// between walkable cells will be calculated.
//	m_chf = rcAllocCompactHeightfield();
//	if (!m_chf)
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Out of memory 'chf'.");
//		return 0;
//	}
//	if (!rcBuildCompactHeightfield(m_ctx, m_cfg.walkableHeight, m_cfg.walkableClimb, *m_solid, *m_chf))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not build compact data.");
//		return 0;
//	}

//	if (!m_keepInterResults)
//	{
//		rcFreeHeightField(m_solid);
//		m_solid = 0;
//	}

//	// Erode the walkable area by agent radius.
//	if (!rcErodeWalkableArea(m_ctx, m_cfg.walkableRadius, *m_chf))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not erode.");
//		return 0;
//	}

//	// (Optional) Mark areas.
//	const ConvexVolume* vols = m_geom->getConvexVolumes();
//	for (int i  = 0; i < m_geom->getConvexVolumeCount(); ++i)
//		rcMarkConvexPolyArea(m_ctx, vols[i].verts, vols[i].nverts, vols[i].hmin, vols[i].hmax, (unsigned char)vols[i].area, *m_chf);


//	// Partition the heightfield so that we can use simple algorithm later to triangulate the walkable areas.
//	// There are 3 martitioning methods, each with some pros and cons:
//	// 1) Watershed partitioning
//	//   - the classic Recast partitioning
//	//   - creates the nicest tessellation
//	//   - usually slowest
//	//   - partitions the heightfield into nice regions without holes or overlaps
//	//   - the are some corner cases where this method creates produces holes and overlaps
//	//      - holes may appear when a small obstacles is close to large open area (triangulation can handle this)
//	//      - overlaps may occur if you have narrow spiral corridors (i.e stairs), this make triangulation to fail
//	//   * generally the best choice if you precompute the nacmesh, use this if you have large open areas
//	// 2) Monotone partioning
//	//   - fastest
//	//   - partitions the heightfield into regions without holes and overlaps (guaranteed)
//	//   - creates long thin polygons, which sometimes causes paths with detours
//	//   * use this if you want fast navmesh generation
//	// 3) Layer partitoining
//	//   - quite fast
//	//   - partitions the heighfield into non-overlapping regions
//	//   - relies on the triangulation code to cope with holes (thus slower than monotone partitioning)
//	//   - produces better triangles than monotone partitioning
//	//   - does not have the corner cases of watershed partitioning
//	//   - can be slow and create a bit ugly tessellation (still better than monotone)
//	//     if you have large open areas with small obstacles (not a problem if you use tiles)
//	//   * good choice to use for tiled navmesh with medium and small sized tiles

//	if (m_partitionType == SAMPLE_PARTITION_WATERSHED)
//	{
//		// Prepare for region partitioning, by calculating distance field along the walkable surface.
//		if (!rcBuildDistanceField(m_ctx, *m_chf))
//		{
//			m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not build distance field.");
//			return 0;
//		}

//		// Partition the walkable surface into simple regions without holes.
//		if (!rcBuildRegions(m_ctx, *m_chf, 0, m_cfg.minRegionArea, m_cfg.mergeRegionArea))
//		{
//			m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not build watershed regions.");
//			return 0;
//		}
//	}
//	else if (m_partitionType == SAMPLE_PARTITION_MONOTONE)
//	{
//		// Partition the walkable surface into simple regions without holes.
//		// Monotone partitioning does not need distancefield.
//		if (!rcBuildRegionsMonotone(m_ctx, *m_chf, 0, m_cfg.minRegionArea, m_cfg.mergeRegionArea))
//		{
//			m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not build monotone regions.");
//			return 0;
//		}
//	}
//	else // SAMPLE_PARTITION_LAYERS
//	{
//		// Partition the walkable surface into simple regions without holes.
//		if (!rcBuildLayerRegions(m_ctx, *m_chf, 0, m_cfg.minRegionArea))
//		{
//			m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not build layer regions.");
//			return 0;
//		}
//	}

//	//
//	// Step 5. Trace and simplify region contours.
//	//

//	// Create contours.
//	m_cset = rcAllocContourSet();
//	if (!m_cset)
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Out of memory 'cset'.");
//		return 0;
//	}
//	if (!rcBuildContours(m_ctx, *m_chf, m_cfg.maxSimplificationError, m_cfg.maxEdgeLen, *m_cset))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not create contours.");
//		return 0;
//	}

//	//
//	// Step 6. Build polygons mesh from contours.
//	//

//	// Build polygon navmesh from the contours.
//	m_pmesh = rcAllocPolyMesh();
//	if (!m_pmesh)
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Out of memory 'pmesh'.");
//		return 0;
//	}
//	if (!rcBuildPolyMesh(m_ctx, *m_cset, m_cfg.maxVertsPerPoly, *m_pmesh))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not triangulate contours.");
//		return 0;
//	}

//	//
//	// Step 7. Create detail mesh which allows to access approximate height on each polygon.
//	//

//	m_dmesh = rcAllocPolyMeshDetail();
//	if (!m_dmesh)
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Out of memory 'pmdtl'.");
//		return 0;
//	}

//	if (!rcBuildPolyMeshDetail(m_ctx, *m_pmesh, *m_chf, m_cfg.detailSampleDist, m_cfg.detailSampleMaxError, *m_dmesh))
//	{
//		m_ctx->log(RC_LOG_ERROR, "buildNavigation: Could not build detail mesh.");
//		return 0;
//	}

//	if (!m_keepInterResults)
//	{
//		rcFreeCompactHeightfield(m_chf);
//		m_chf = 0;
//		rcFreeContourSet(m_cset);
//		m_cset = 0;
//	}

//	// At this point the navigation mesh data is ready, you can access it from m_pmesh.
//	// See duDebugDrawPolyMesh or dtCreateNavMeshData as examples how to access the data.

//	//
//	// (Optional) Step 8. Create Detour data from Recast poly mesh.
//	//

//	// The GUI may allow more max points per polygon than Detour can handle.
//	// Only build the detour navmesh if we do not exceed the limit.
//	if (m_cfg.maxVertsPerPoly <= DT_VERTS_PER_POLYGON)
//	{
//		unsigned char* navData = 0;
//		int navDataSize = 0;

//		// Update poly flags from areas.
//		for (int i = 0; i < m_pmesh->npolys; ++i)
//		{
//			if (m_pmesh->areas[i] == RC_WALKABLE_AREA)
//				m_pmesh->areas[i] = SAMPLE_POLYAREA_GROUND;

//			if (m_pmesh->areas[i] == SAMPLE_POLYAREA_GROUND ||
//				m_pmesh->areas[i] == SAMPLE_POLYAREA_GRASS ||
//				m_pmesh->areas[i] == SAMPLE_POLYAREA_ROAD)
//			{
//				m_pmesh->flags[i] = SAMPLE_POLYFLAGS_WALK;
//			}
//			else if (m_pmesh->areas[i] == SAMPLE_POLYAREA_WATER)
//			{
//				m_pmesh->flags[i] = SAMPLE_POLYFLAGS_SWIM;
//			}
//			else if (m_pmesh->areas[i] == SAMPLE_POLYAREA_DOOR)
//			{
//				m_pmesh->flags[i] = SAMPLE_POLYFLAGS_WALK | SAMPLE_POLYFLAGS_DOOR;
//			}
//		}


//		dtNavMeshCreateParams params;
//		memset(&params, 0, sizeof(params));
//		params.verts = m_pmesh->verts;
//		params.vertCount = m_pmesh->nverts;
//		params.polys = m_pmesh->polys;
//		params.polyAreas = m_pmesh->areas;
//		params.polyFlags = m_pmesh->flags;
//		params.polyCount = m_pmesh->npolys;
//		params.nvp = m_pmesh->nvp;
//		params.detailMeshes = m_dmesh->meshes;
//		params.detailVerts = m_dmesh->verts;
//		params.detailVertsCount = m_dmesh->nverts;
//		params.detailTris = m_dmesh->tris;
//		params.detailTriCount = m_dmesh->ntris;
//		params.offMeshConVerts = m_geom->getOffMeshConnectionVerts();
//		params.offMeshConRad = m_geom->getOffMeshConnectionRads();
//		params.offMeshConDir = m_geom->getOffMeshConnectionDirs();
//		params.offMeshConAreas = m_geom->getOffMeshConnectionAreas();
//		params.offMeshConFlags = m_geom->getOffMeshConnectionFlags();
//		params.offMeshConUserID = m_geom->getOffMeshConnectionId();
//		params.offMeshConCount = m_geom->getOffMeshConnectionCount();
//		params.walkableHeight = m_agentHeight;
//		params.walkableRadius = m_agentRadius;
//		params.walkableClimb = m_agentMaxClimb;
//		rcVcopy(params.bmin, m_pmesh->bmin);
//		rcVcopy(params.bmax, m_pmesh->bmax);
//		params.cs = m_cfg.cs;
//		params.ch = m_cfg.ch;
//		params.buildBvTree = true;

//		if (!dtCreateNavMeshData(&params, &navData, &navDataSize))
//		{
//			m_ctx->log(RC_LOG_ERROR, "Could not build Detour navmesh.");
//			return 0;
//		}

//		m_navMesh = dtAllocNavMesh();
//		if (!m_navMesh)
//		{
//			dtFree(navData);
//			m_ctx->log(RC_LOG_ERROR, "Could not create Detour navmesh");
//			return 0;
//		}

//		dtStatus status;

//		status = m_navMesh->init(navData, navDataSize, DT_TILE_FREE_DATA);
//		if (dtStatusFailed(status))
//		{
//			dtFree(navData);
//			m_ctx->log(RC_LOG_ERROR, "Could not init Detour navmesh");
//			return 0;
//		}

//		status = m_navQuery->init(m_navMesh, 2048);
//		if (dtStatusFailed(status))
//		{
//			m_ctx->log(RC_LOG_ERROR, "Could not init Detour navmesh query");
//			return 0;
//		}
//	}

//	m_ctx->stopTimer(RC_TIMER_TOTAL);

//	// Show performance stats.
//	duLogBuildTimes(*m_ctx, m_ctx->getAccumulatedTime(RC_TIMER_TOTAL));
//	m_ctx->log(RC_LOG_PROGRESS, ">> Polymesh: %d vertices  %d polygons", m_pmesh->nverts, m_pmesh->npolys);

//	m_totalBuildTimeMs = m_ctx->getAccumulatedTime(RC_TIMER_TOTAL)/1000.0f;

//	if (m_tool)
//		m_tool->init(this);
//	initToolStates(this);

//	return true;
//}


int freeNavMesh(struct recast_polyMesh_holder *pmeshHolder, struct recast_polyMeshDetail_holder *dmeshHolder,
                char *reports, int reportsMaxChars) {

    /* clear reports string */
    strncpy(reports, "", reportsMaxChars);

    if(pmeshHolder) {
        recast_destroyPolyMesh(pmeshHolder->pmesh);
    }
    if(dmeshHolder) {
        recast_destroyPolyMeshDetail(dmeshHolder->dmesh);
    }

    return 1;
}

//static Object *createRepresentation(bContext *C, struct recast_polyMesh *pmesh, struct recast_polyMeshDetail *dmesh,
//                                  Base *base, unsigned int lay)
//{
//	float co[3], rot[3];
//	BMEditMesh *em;
//	int i, j, k;
//	unsigned short *v;
//	int face[3];
//	Scene *scene = CTX_data_scene(C);
//	Object *obedit;
//	int createob = base == NULL;
//	int nverts, nmeshes, nvp;
//	unsigned short *verts, *polys;
//	unsigned int *meshes;
//	float bmin[3], cs, ch, *dverts;
//	unsigned char *tris;

//	zero_v3(co);
//	zero_v3(rot);

//	if (createob) {
//		/* create new object */
//		obedit = ED_object_add_type(C, OB_MESH, "Navmesh", co, rot, false, lay);
//	}
//	else {
//		obedit = base->object;
//		BKE_scene_base_deselect_all(scene);
//		BKE_scene_base_select(scene, base);
//		copy_v3_v3(obedit->loc, co);
//		copy_v3_v3(obedit->rot, rot);
//	}

//	ED_object_editmode_enter(C, EM_DO_UNDO | EM_IGNORE_LAYER);
//	em = BKE_editmesh_from_object(obedit);

//	if (!createob) {
//		/* clear */
//		EDBM_mesh_clear(em);
//	}

//	/* create verts for polygon mesh */
//	verts = recast_polyMeshGetVerts(pmesh, &nverts);
//	recast_polyMeshGetBoundbox(pmesh, bmin, NULL);
//	recast_polyMeshGetCell(pmesh, &cs, &ch);

//	for (i = 0; i < nverts; i++) {
//		v = &verts[3 * i];
//		co[0] = bmin[0] + v[0] * cs;
//		co[1] = bmin[1] + v[1] * ch;
//		co[2] = bmin[2] + v[2] * cs;
//		SWAP(float, co[1], co[2]);
//		BM_vert_create(em->bm, co, NULL, BM_CREATE_NOP);
//	}

//	/* create custom data layer to save polygon idx */
//	CustomData_add_layer_named(&em->bm->pdata, CD_RECAST, CD_CALLOC, NULL, 0, "createRepresentation recastData");
//	CustomData_bmesh_init_pool(&em->bm->pdata, 0, BM_FACE);
	
//	/* create verts and faces for detailed mesh */
//	meshes = recast_polyMeshDetailGetMeshes(dmesh, &nmeshes);
//	polys = recast_polyMeshGetPolys(pmesh, NULL, &nvp);
//	dverts = recast_polyMeshDetailGetVerts(dmesh, NULL);
//	tris = recast_polyMeshDetailGetTris(dmesh, NULL);

//	for (i = 0; i < nmeshes; i++) {
//		int uniquevbase = em->bm->totvert;
//		unsigned int vbase = meshes[4 * i + 0];
//		unsigned short ndv = meshes[4 * i + 1];
//		unsigned short tribase = meshes[4 * i + 2];
//		unsigned short trinum = meshes[4 * i + 3];
//		const unsigned short *p = &polys[i * nvp * 2];
//		int nv = 0;

//		for (j = 0; j < nvp; ++j) {
//			if (p[j] == 0xffff) break;
//			nv++;
//		}

//		/* create unique verts  */
//		for (j = nv; j < ndv; j++) {
//			copy_v3_v3(co, &dverts[3 * (vbase + j)]);
//			SWAP(float, co[1], co[2]);
//			BM_vert_create(em->bm, co, NULL, BM_CREATE_NOP);
//		}

//		/* need to rebuild entirely because array size changes */
//		BM_mesh_elem_table_init(em->bm, BM_VERT);

//		/* create faces */
//		for (j = 0; j < trinum; j++) {
//			unsigned char *tri = &tris[4 * (tribase + j)];
//			BMFace *newFace;
//			int *polygonIdx;

//			for (k = 0; k < 3; k++) {
//				if (tri[k] < nv)
//					face[k] = p[tri[k]];  /* shared vertex */
//				else
//					face[k] = uniquevbase + tri[k] - nv;  /* unique vertex */
//			}
//			newFace = BM_face_create_quad_tri(em->bm,
//			                                  BM_vert_at_index(em->bm, face[0]),
//			                                  BM_vert_at_index(em->bm, face[2]),
//			                                  BM_vert_at_index(em->bm, face[1]), NULL,
//			                                  NULL, BM_CREATE_NOP);

//			/* set navigation polygon idx to the custom layer */
//			polygonIdx = (int *)CustomData_bmesh_get(&em->bm->pdata, newFace->head.data, CD_RECAST);
//			*polygonIdx = i + 1; /* add 1 to avoid zero idx */
//		}
//	}

//	recast_destroyPolyMesh(pmesh);
//	recast_destroyPolyMeshDetail(dmesh);

//	DAG_id_tag_update((ID *)obedit->data, OB_RECALC_DATA);
//	WM_event_add_notifier(C, NC_GEOM | ND_DATA, obedit->data);


//	ED_object_editmode_exit(C, EM_FREEDATA);
//	WM_event_add_notifier(C, NC_OBJECT | ND_DRAW, obedit);

//	if (createob) {
//		obedit->gameflag &= ~OB_COLLISION;
//		obedit->gameflag |= OB_NAVMESH;
//		obedit->body_type = OB_BODY_TYPE_NAVMESH;
//	}

//	BKE_mesh_ensure_navmesh(obedit->data);

//	return obedit;
//}

//static int navmesh_create_exec(bContext *C, wmOperator *op)
//{
//	Scene *scene = CTX_data_scene(C);
//	LinkNode *obs = NULL;
//	Base *navmeshBase = NULL;

//	CTX_DATA_BEGIN (C, Base *, base, selected_editable_bases)
//	{
//		if (base->object->type == OB_MESH) {
//			if (base->object->body_type == OB_BODY_TYPE_NAVMESH) {
//				if (!navmeshBase || base == scene->basact) {
//					navmeshBase = base;
//				}
//			}
//			else {
//				BLI_linklist_prepend(&obs, base->object);
//			}
//		}
//	}
//	CTX_DATA_END;

//	if (obs) {
//		struct recast_polyMesh *pmesh = NULL;
//		struct recast_polyMeshDetail *dmesh = NULL;
//		bool ok;
//		unsigned int lay = 0;

//		int nverts = 0, ntris = 0;
//		int *tris = NULL;
//		float *verts = NULL;

//		createVertsTrisData(C, obs, &nverts, &verts, &ntris, &tris, &lay);
//		BLI_linklist_free(obs, NULL);
//		if ((ok = buildNavMesh(&scene->gm.recastData, nverts, verts, ntris, tris, &pmesh, &dmesh, op->reports))) {
//			createRepresentation(C, pmesh, dmesh, navmeshBase, lay);
//		}

//		MEM_freeN(verts);
//		MEM_freeN(tris);

//		return ok ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
//	}
//	else {
//		BKE_report(op->reports, RPT_ERROR, "No mesh objects found");

//		return OPERATOR_CANCELLED;
//	}
//}

//void MESH_OT_navmesh_make(wmOperatorType *ot)
//{
//	/* identifiers */
//	ot->name = "Create Navigation Mesh";
//	ot->description = "Create navigation mesh for selected objects";
//	ot->idname = "MESH_OT_navmesh_make";

//	/* api callbacks */
//	ot->exec = navmesh_create_exec;

//	/* flags */
//	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
//}

//static int navmesh_face_copy_exec(bContext *C, wmOperator *op)
//{
//	Object *obedit = CTX_data_edit_object(C);
//	BMEditMesh *em = BKE_editmesh_from_object(obedit);

//	/* do work here */
//	BMFace *efa_act = BM_mesh_active_face_get(em->bm, false, false);

//	if (efa_act) {
//		if (CustomData_has_layer(&em->bm->pdata, CD_RECAST)) {
//			BMFace *efa;
//			BMIter iter;
//			int targetPolyIdx = *(int *)CustomData_bmesh_get(&em->bm->pdata, efa_act->head.data, CD_RECAST);
//			targetPolyIdx = targetPolyIdx >= 0 ? targetPolyIdx : -targetPolyIdx;

//			if (targetPolyIdx > 0) {
//				/* set target poly idx to other selected faces */
//				BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {
//					if (BM_elem_flag_test(efa, BM_ELEM_SELECT) && efa != efa_act) {
//						int *recastDataBlock = (int *)CustomData_bmesh_get(&em->bm->pdata, efa->head.data, CD_RECAST);
//						*recastDataBlock = targetPolyIdx;
//					}
//				}
//			}
//			else {
//				BKE_report(op->reports, RPT_ERROR, "Active face has no index set");
//			}
//		}
//	}

//	DAG_id_tag_update((ID *)obedit->data, OB_RECALC_DATA);
//	WM_event_add_notifier(C, NC_GEOM | ND_DATA, obedit->data);

//	return OPERATOR_FINISHED;
//}

//void MESH_OT_navmesh_face_copy(struct wmOperatorType *ot)
//{
//	/* identifiers */
//	ot->name = "NavMesh Copy Face Index";
//	ot->description = "Copy the index from the active face";
//	ot->idname = "MESH_OT_navmesh_face_copy";

//	/* api callbacks */
//	ot->poll = ED_operator_editmesh;
//	ot->exec = navmesh_face_copy_exec;

//	/* flags */
//	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
//}

//static int compare(const void *a, const void *b)
//{
//	return (*(int *)a - *(int *)b);
//}

//static int findFreeNavPolyIndex(BMEditMesh *em)
//{
//	/* construct vector of indices */
//	int numfaces = em->bm->totface;
//	int *indices = MEM_callocN(sizeof(int) * numfaces, "findFreeNavPolyIndex(indices)");
//	BMFace *ef;
//	BMIter iter;
//	int i, idx = em->bm->totface - 1, freeIdx = 1;

//	/*XXX this originally went last to first, but that isn't possible anymore*/
//	BM_ITER_MESH (ef, &iter, em->bm, BM_FACES_OF_MESH) {
//		int polyIdx = *(int *)CustomData_bmesh_get(&em->bm->pdata, ef->head.data, CD_RECAST);
//		indices[idx] = polyIdx;
//		idx--;
//	}

//	qsort(indices, numfaces, sizeof(int), compare);

//	/* search first free index */
//	freeIdx = 1;
//	for (i = 0; i < numfaces; i++) {
//		if (indices[i] == freeIdx)
//			freeIdx++;
//		else if (indices[i] > freeIdx)
//			break;
//	}

//	MEM_freeN(indices);

//	return freeIdx;
//}

//static int navmesh_face_add_exec(bContext *C, wmOperator *UNUSED(op))
//{
//	Object *obedit = CTX_data_edit_object(C);
//	BMEditMesh *em = BKE_editmesh_from_object(obedit);
//	BMFace *ef;
//	BMIter iter;
	
//	if (CustomData_has_layer(&em->bm->pdata, CD_RECAST)) {
//		int targetPolyIdx = findFreeNavPolyIndex(em);

//		if (targetPolyIdx > 0) {
//			/* set target poly idx to selected faces */
//			/*XXX this originally went last to first, but that isn't possible anymore*/
			
//			BM_ITER_MESH (ef, &iter, em->bm, BM_FACES_OF_MESH) {
//				if (BM_elem_flag_test(ef, BM_ELEM_SELECT)) {
//					int *recastDataBlock = (int *)CustomData_bmesh_get(&em->bm->pdata, ef->head.data, CD_RECAST);
//					*recastDataBlock = targetPolyIdx;
//				}
//			}
//		}
//	}

//	DAG_id_tag_update((ID *)obedit->data, OB_RECALC_DATA);
//	WM_event_add_notifier(C, NC_GEOM | ND_DATA, obedit->data);

//	return OPERATOR_FINISHED;
//}

//void MESH_OT_navmesh_face_add(struct wmOperatorType *ot)
//{
//	/* identifiers */
//	ot->name = "NavMesh New Face Index";
//	ot->description = "Add a new index and assign it to selected faces";
//	ot->idname = "MESH_OT_navmesh_face_add";

//	/* api callbacks */
//	ot->poll = ED_operator_editmesh;
//	ot->exec = navmesh_face_add_exec;

//	/* flags */
//	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
//}

//static int navmesh_obmode_data_poll(bContext *C)
//{
//	Object *ob = ED_object_active_context(C);
//	if (ob && (ob->mode == OB_MODE_OBJECT) && (ob->type == OB_MESH)) {
//		Mesh *me = ob->data;
//		return CustomData_has_layer(&me->pdata, CD_RECAST);
//	}
//	return false;
//}

//static int navmesh_obmode_poll(bContext *C)
//{
//	Object *ob = ED_object_active_context(C);
//	if (ob && (ob->mode == OB_MODE_OBJECT) && (ob->type == OB_MESH)) {
//		return true;
//	}
//	return false;
//}

//static int navmesh_reset_exec(bContext *C, wmOperator *UNUSED(op))
//{
//	Object *ob = ED_object_active_context(C);
//	Mesh *me = ob->data;

//	CustomData_free_layers(&me->pdata, CD_RECAST, me->totpoly);

//	BKE_mesh_ensure_navmesh(me);

//	DAG_id_tag_update(&me->id, OB_RECALC_DATA);
//	WM_event_add_notifier(C, NC_GEOM | ND_DATA, &me->id);

//	return OPERATOR_FINISHED;
//}

//void MESH_OT_navmesh_reset(struct wmOperatorType *ot)
//{
//	/* identifiers */
//	ot->name = "NavMesh Reset Index Values";
//	ot->description = "Assign a new index to every face";
//	ot->idname = "MESH_OT_navmesh_reset";

//	/* api callbacks */
//	ot->poll = navmesh_obmode_poll;
//	ot->exec = navmesh_reset_exec;

//	/* flags */
//	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
//}

//static int navmesh_clear_exec(bContext *C, wmOperator *UNUSED(op))
//{
//	Object *ob = ED_object_active_context(C);
//	Mesh *me = ob->data;

//	CustomData_free_layers(&me->pdata, CD_RECAST, me->totpoly);

//	DAG_id_tag_update(&me->id, OB_RECALC_DATA);
//	WM_event_add_notifier(C, NC_GEOM | ND_DATA, &me->id);

//	return OPERATOR_FINISHED;
//}

//void MESH_OT_navmesh_clear(struct wmOperatorType *ot)
//{
//	/* identifiers */
//	ot->name = "NavMesh Clear Data";
//	ot->description = "Remove navmesh data from this mesh";
//	ot->idname = "MESH_OT_navmesh_clear";

//	/* api callbacks */
//	ot->poll = navmesh_obmode_data_poll;
//	ot->exec = navmesh_clear_exec;

//	/* flags */
//	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
//}
