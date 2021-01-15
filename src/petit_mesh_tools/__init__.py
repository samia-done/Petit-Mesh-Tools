# Copyright (c) 2020 Samia
import os
import codecs
import csv

if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(operator)
    importlib.reload(preferences)
    importlib.reload(updater)
else:
    import bpy
    from . import utils
    from . import operator
    from . import preferences
    from . import updater

import bpy

bl_info = {
    "name": "Petit Mesh Tools",
    "author": "Samia",
    "version": (0, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Edit Tab",
    "description": "Petit Mesh Tools",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/samia-done/Petit-Mesh-Tools",
    "tracker_url": "https://github.com/samia-done/Petit-Mesh-Tools/issues",
    "category": "Mesh"
}

classes = (
    preferences.PMT_AddonPreferences,
    updater.PMT_OT_CheckAddonUpdate,
    updater.PMT_OT_UpdateAddon,
    operator.PMT_ToolSettings,
    operator.PMT_OT_mesh_extrude_loop_to_region,
    operator.VIEW3D_PT_edit_petit_mesh_tools
)


def make_annotations(cls):
    if bpy.app.version < (2, 80):
        return cls
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


# 翻訳辞書の取得
def get_translation_dict():
    translation_dict = {}
    path = os.path.join(os.path.dirname(__file__), "translation_dictionary.csv")
    with codecs.open(path, 'r', 'utf-8') as f:
        reader = csv.reader(f)
        translation_dict['ja_JP'] = {}
        for row in reader:
            for context in bpy.app.translations.contexts:
                translation_dict['ja_JP'][(context, row[1])] = row[0]
    return translation_dict


# def menu_func(self, context):
#     self.layout.separator()


# def register_menu():


# def unregister_menu():


def register():
    updater.register_updater(bl_info)

    for cls in classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)
    bpy.types.Scene.PMT_ToolSettings = bpy.props.PointerProperty(type=operator.PMT_ToolSettings)
    preferences.update_panel(None, bpy.context)

    bpy.app.translations.register(__name__, get_translation_dict())


def unregister():
    bpy.app.translations.unregister(__name__)

    del bpy.types.Scene.PMT_ToolSettings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
