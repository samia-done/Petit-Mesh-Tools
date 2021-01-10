# Copyright (c) 2020 Samia

import bpy

from .utils.addon_updater import AddonUpdaterManager
from . import updater
from . import operator


def get_update_candidate_branches(_, __):
    manager = AddonUpdaterManager.get_instance()
    if not manager.candidate_checked():
        return []

    return [(name, name, "") for name in manager.get_candidate_branch_names()]

# Define Panel classes for updating


def update_panel(self, context):
    panels = (
        operator.VIEW3D_PT_edit_petit_mesh_tools,
    )
    message = "Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__package__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class PMT_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    category: bpy.props.StringProperty(
        name="Tab Category",
        description="Choose a name for the category of the panel",
        default="Edit"
    )

    # for add-on updater
    updater_branch_to_update: bpy.props.EnumProperty(
        name="branch",
        description="Target branch to update add-on",
        items=get_update_candidate_branches
    )

    def __init__(self):
        super(bpy.types.AddonPreferences, self).__init__()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")
        updater.draw_updater_ui(self)
