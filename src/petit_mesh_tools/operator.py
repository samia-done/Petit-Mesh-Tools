from typing import Tuple, Iterator
import bpy
import bmesh
import copy
import time
import mathutils
from bmesh.types import BMFace
from bpy.types import OperatorProperties


class PMT_ToolSettings(bpy.types.PropertyGroup):

    # scale: bpy.props.FloatVectorProperty(
    #     name="Scale",
    #     description="Scale",
    #     default=[1.3, 1.3, 1.3],
    #     subtype="XYZ",
    #     size=3,
    #     min=0.0,
    #     options={'HIDDEN'}
    # )
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale",
        default=1.3,
        min=0.0,
        options={'HIDDEN'}
    )

    display_extrude_loop: bpy.props.BoolProperty(
        name="Extrude loop settings",
        description="Scale",
        default=True,
        options={'HIDDEN'}
    )


class PMT_OT_mesh_extrude_loop_to_region(bpy.types.Operator):

    bl_idname = "mesh.pmt_extrude_loop_to_region"
    bl_label = "Extrude Loop Inner-Region"
    bl_description = "Extrude the face that is inside the selected edge loop"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.active_object = None
        self.bm = None
        self.selected_edges = []

    def get_selected_edges(self, context):

        self.active_object = context.active_object
        self.active_object.update_from_editmode()

        self.bm = bmesh.new()
        self.bm = bmesh.from_edit_mesh(self.active_object.data)

        if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 73:
            self.bm.verts.ensure_lookup_table()
            self.bm.faces.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()

        selected_edges = []

        for e in self.bm.select_history:
            if isinstance(e, bmesh.types.BMEdge):
                selected_edges.append(e)

        return selected_edges

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH' and (obj.mode == 'EDIT'):
            return True
        return False

    def invoke(self, context, event):
        self.selected_edges = self.get_selected_edges(context)

        if len(self.selected_edges) >= 2:
            return self.execute(context)
        else:
            self.report({'ERROR'}, "Select at least two edge loops")
            return {'FINISHED'}

    def execute(self, context):
        current_transform_pivot_point = copy.copy(bpy.context.scene.tool_settings.transform_pivot_point)
        bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'

        pmt_tool_settings: PMT_ToolSettings = context.scene.PMT_ToolSettings
        # _scale = (pmt_tool_settings.scale[0], pmt_tool_settings.scale[1], pmt_tool_settings.scale[2])
        _scale = (pmt_tool_settings.scale, pmt_tool_settings.scale, pmt_tool_settings.scale)

        bpy.ops.mesh.select_all(action='DESELECT')

        new_edges = []
        for i, e in enumerate(self.selected_edges):
            e.select = True
            # print("エッジの境界:", e.is_boundary)

            bpy.ops.mesh.loop_multi_select(ring=False)
            bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode": 1},
                                        TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_type": 'GLOBAL',
                                            "orient_matrix": ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                                            "orient_matrix_type": 'GLOBAL', "constraint_axis": (False, False, False),
                                            "mirror": False, "use_proportional_edit": False,
                                            "proportional_edit_falloff": 'SMOOTH', "proportional_size": 1,
                                            "use_proportional_connected": False, "use_proportional_projected": False,
                                            "snap": False, "snap_target": 'CLOSEST', "snap_point": (0, 0, 0),
                                            "snap_align": False, "snap_normal": (0, 0, 0), "gpencil_strokes": False,
                                            "cursor_transform": False, "texture_space": False,
                                            "remove_on_cancel": False,
                                            "release_confirm": False, "use_accurate": False})

            bpy.ops.transform.resize(value=_scale, orient_type='GLOBAL',
                                     orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                     mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                                     proportional_size=1, use_proportional_connected=False,
                                     use_proportional_projected=False)

            for new_edge in self.bm.edges:  # type: bmesh.types.BMEdge
                if new_edge.select:
                    new_edges.append(new_edge)
                    break

            bpy.ops.mesh.select_all(action='DESELECT')

        new_edges.insert(0, self.selected_edges[0])
        new_edges.append(self.selected_edges[-1])

        for i, e in enumerate(self.selected_edges):
            e.select = True

        bpy.ops.mesh.loop_multi_select(ring=False)
        bpy.ops.mesh.loop_to_region()
        bpy.ops.mesh.delete(type='FACE')

        count = len(new_edges)-1
        for i in range(count):
            if 0 < i < count:
                new_edges[i].select = True
                new_edges[i + 1].select = True
                bpy.ops.mesh.loop_multi_select(ring=False)
                bpy.ops.mesh.bridge_edge_loops()
                bpy.ops.mesh.select_all(action='DESELECT')

        new_edges[0].select = True
        new_edges[1].select = True
        bpy.ops.mesh.loop_multi_select(ring=False)
        bpy.ops.mesh.bridge_edge_loops()
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.context.scene.tool_settings.transform_pivot_point = current_transform_pivot_point

        return {'FINISHED'}


class VIEW3D_PT_edit_putit_mesh_tools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Edit'
    bl_context = "mesh_edit"
    bl_label = "Putit Mesh Tools"
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context: bpy.types.Context):
        pmt_tool_settings: PMT_ToolSettings = context.scene.PMT_ToolSettings

        layout = self.layout
        col = layout.column(align=True)

        split = col.split(factor=0.15, align=True)
        if pmt_tool_settings.display_extrude_loop:
            split.prop(pmt_tool_settings, "display_extrude_loop", text="", icon='DOWNARROW_HLT')
        else:
            split.prop(pmt_tool_settings, "display_extrude_loop", text="", icon='RIGHTARROW')

        split.operator_context = 'INVOKE_DEFAULT'
        op = split.operator(PMT_OT_mesh_extrude_loop_to_region.bl_idname, text=PMT_OT_mesh_extrude_loop_to_region.bl_label)  # type: PMT_OT_mesh_extrude_loop_to_region

        # extrude loop - settings
        if pmt_tool_settings.display_extrude_loop:
            box = col.column(align=True).box().column()
            box.prop(pmt_tool_settings, "scale")
