import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from shapely.geometry import MultiPolygon,Polygon
from shapely.ops import cascaded_union

#from data_extractor import CellDataExtractor

def mpoly_2_pathpatch(mpoly):
    #print(type(mpoly))
    assert isinstance(mpoly, (MultiPolygon, Polygon))

    codes = []
    all_x = []
    all_y = []

    if(isinstance(mpoly, Polygon)):
        mpoly = [mpoly]

    for poly in mpoly:
        x = np.array(poly.exterior)[:,0].tolist()
        y = np.array(poly.exterior)[:,1].tolist()
        # skip boundary between individual rings
        codes += [mpath.Path.MOVETO] + (len(x)-1)*[mpath.Path.LINETO]
        all_x += x
        all_y += y

    carib_path = mpath.Path(np.column_stack((all_x,all_y)), codes)
    carib_patch = mpatches.PathPatch(carib_path)#,lw=0.5,fc='blue', alpha=0.3)#facecolor='none'

    return carib_patch

class ViewerPrep(object):
    def __init__(self, cell_cid_full, cell_shapes_full, catchment_id_map, bbox):
        #self.rm = rm
        self.catchment_id_map = catchment_id_map # self.rm.catchment_id_map
        self.polys = None
        self.patches = None
        self.bbox = bbox # self.rm.bounding_region.geometry
        self.cell_shapes_full = cell_shapes_full # self.rm.gis_info
        #self.cell_data_ext = CellDataExtractor(self.rm)
        self.cell_cid_full = cell_cid_full # self.cell_data_ext.cid

    @staticmethod
    def shp_2_polypatch(polygons):
        if not isinstance(polygons, list):
            polygons = [polygons]
        return [mpoly_2_pathpatch(p) for p in polygons]

    def plot_region(self):
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        # ax.add_collection(PatchCollection([PolygonPatch(p,facecolor=None,edgecolor="black") for p in self.catch_polys], match_original=True))
        ax.add_collection(PatchCollection(self.patches, facecolor='none', edgecolor='blue'))
        ax.set_xlim(self.bbox[0], self.bbox[2])
        ax.set_ylim(self.bbox[1], self.bbox[3])
        plt.show()

    def clip_extent(self):
        #union_poly = cascaded_union(self.polys)
        #self.bbox = union_poly.bounds
        self.bbox = MultiPolygon(polygons=self.polys).bounds


class CellViewerPrep(ViewerPrep):
    def __init__(self, cell_cid_full, cell_shapes_full, catchment_id_map, bbox, catch_select=None, clip=False):
        super().__init__(cell_cid_full, cell_shapes_full, catchment_id_map, bbox)

        if catch_select is None:
            self.catch_ids_select = self.catchment_id_map
            self.cell_idx_select = np.in1d(self.cell_cid_full, self.catchment_id_map).nonzero()[0]
        else:
            self.catch_ids_select = catch_select
            self.cell_idx_select = np.in1d(self.cell_cid_full, catch_select).nonzero()[0]

        #self.cell_idx_select = np.in1d(self.cell_cid_full, self.catch_ids_select).nonzero()[0]
        #self.cell_shapes_select = self.cell_shapes_full[self.cell_idx_select]

        self.ts_fetching_lst = self.cell_idx_select
        self.map_fetching_lst = self.catch_ids_select

        self.polys = self.cell_shapes_full[self.cell_idx_select].tolist()
        self.patches = self.shp_2_polypatch(self.polys)

        if clip:
            self.clip_extent()

class SubcatViewerPrep(ViewerPrep):
    def __init__(self, cell_cid_full, cell_shapes_full, catchment_id_map, bbox, catch_grp=None, clip=False):
        super().__init__(cell_cid_full, cell_shapes_full, catchment_id_map, bbox)

        if catch_grp is None:
            self.catch_ids_select = self.catchment_id_map
            self.catch_grp_select = [[cid] for cid in self.catchment_id_map]
        else:
            self.catch_ids_select = [item for sublist in catch_grp for item in sublist]
            self.catch_grp_select = catch_grp

        self.ts_fetching_lst = self.map_fetching_lst = self.catch_grp_select

        self.polys = [cascaded_union(self.cell_shapes_full[np.in1d(self.cell_cid_full,cid_lst)].tolist())
                      for cid_lst in self.catch_grp_select]
        self.patches = self.shp_2_polypatch(self.polys)

        if clip:
            self.clip_extent()

