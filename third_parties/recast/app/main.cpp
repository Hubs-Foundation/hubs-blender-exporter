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
 * Contributor(s): Przemysław Bągard,
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>
#include <string.h>
#include "recast-capi.h"
#include "mesh_navmesh.h"

int main(int argc, char *argv[])
{
    RecastData recastData;
    recastData.cellsize = 0.300000f;
    recastData.cellheight = 0.200000f;
    recastData.agentmaxslope = 0.785398f;
    recastData.agentmaxclimb = 0.9f;
    recastData.agentheight = 2.0f;
    recastData.agentradius = 0.6f;
    recastData.edgemaxlen = 12.0f;
    recastData.edgemaxerror = 1.3f;
    recastData.regionminsize = 8.0;
    recastData.regionmergesize = 20.0;
    recastData.vertsperpoly = 6;
    recastData.detailsampledist = 6.0;
    recastData.detailsamplemaxerror = 1.0;
    recastData.partitioning = 0;
    recastData.pad1 = 0;

    int reportsMaxChars = 128;
    char msg[128];
    strncpy(msg, "", reportsMaxChars);

    int nverts = 12;
    const int ntris = 14;
    float verts[] = {
      1.000000, 1.000000, -1.000000,
      1.000000, -1.000000, -1.000000,
      1.000000, 1.000000, 1.000000,
      1.000000, -1.000000, 1.000000,
      -1.000000, 1.000000, -1.000000,
      -1.000000, -1.000000, -1.000000,
      -1.000000, 1.000000, 1.000000,
      -1.000000, -1.000000, 1.000000,
      -10.000000, 0.000000, 10.000000,
      10.000000, 0.000000, 10.000000,
      -10.000000, 0.000000, -10.000000,
      10.000000, 0.000000, -10.000000
    };
    int tris[] = {
        4, 2, 0,
        2, 7, 3,
        6, 5, 7,
        1, 7, 5,
        0, 3, 1,
        4, 1, 5,
        4, 6, 2,
        2, 6, 7,
        6, 4, 5,
        1, 3, 7,
        0, 2, 3,
        4, 0, 1,
        9, 10, 8,
        9, 11, 10
    };

    for (int i = 0; i < ntris; ++i) {
        for (int j = 0; j < 3; ++j) {
            int vertexIndex = tris[i*3+j];
            printf("trisVertex[%i][%i] = (%f, %f, %f)\n", i, j, verts[vertexIndex*3+0], verts[vertexIndex*3+1], verts[vertexIndex*3+2]);
        }
    }


    struct recast_polyMesh_holder pmeshHolder;
    struct recast_polyMeshDetail_holder dmeshHolder;

    int result = buildNavMesh(&recastData, nverts, verts, ntris, tris,
                              &pmeshHolder, &dmeshHolder,
                              msg, reportsMaxChars);

//    int buildNavMesh(const RecastData *recastParams, int nverts, float *verts, int ntris, int *tris,
//                     struct recast_polyMesh_holder *pmeshHolder, struct recast_polyMeshDetail_holder *dmeshHolder,
//                     char *reports, int reportsMaxChars)

    freeNavMesh(&pmeshHolder, &dmeshHolder, msg, reportsMaxChars);

    return 0;
}
