bl_info = {
    "name": "Datablock Bookmarker",
    "category": "System",
    "blender": (2,80,0),
    "version": (0,2)}
import pathlib
import bpy
from bl_operators.presets import AddPresetBase
from bl_ui.utils import PresetPanel

# from pathlib import Path
# from bpy.types import (
    # Panel,Operator,AddonPreferences,Menu,WindowManager,PropertyGroup,
    # VIEW3D_MT_object,VIEW3D_MT_add)
# from bpy.utils import (
    # register_class,unregister_class,preset_paths,user_resource)
# from bpy.props import (
    # PointerProperty,BoolProperty,StringProperty)


def _(a=None,b=[]):
    if a:
        b.append(a)
        return a
    else:
        return b

def get_targetpath(context):
    return pathlib.Path(
        context.preferences.addons[__package__].preferences.getlib(context))

@_
class DBBM_OT_send(bpy.types.Operator):
    bl_idname = "dbbm.send"
    bl_label = "bookmark"
    overwrite: bpy.props.BoolProperty()
    bl_options = {"INTERNAL"}
    def draw(self,context):
        self.layout.prop(self,"overwrite")
        box = self.layout.box()
        box.label(text=str(len(context.selected_objects)))
        for ob in context.selected_objects:
            box.label(text=ob.name)
    def invoke(self,context,event):
        context.window_manager.invoke_props_dialog(self)
        return {"RUNNING_MODAL"}
    def execute(self,context):
        targetpath = get_targetpath(context)
        for ob in context.selected_objects:
            filepath = targetpath / (bpy.path.clean_name(ob.name) + ".blend")
            if filepath.exists() and not self.overwrite:
                self.report({"WARNING"},"file exists:"+str(filepath))
            bpy.data.libraries.write(
                str(filepath),
                set([ob]),
                fake_user=True)
            context.window_manager.dbbm["dbbm_string"] = "|".join((
                    ob.type,ob.name,str(filepath)))
            bpy.ops.dbbm.add_preset(name=filepath.stem)
            self.report({"INFO"},"file written: " + str(filepath))
        return {"FINISHED"}


@_
class DBBM_PT_bookmarks(bpy.types.Panel):
    bl_label = "DBBM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DBBM"
    def draw_header_preset(self,context):
        DBBM_PT_presets.draw_panel_header(self.layout)
    def draw(self,context):
        layout = self.layout
        lib = str(get_targetpath(context))
        layout.operator("wm.path_open",text=lib).filepath = lib
        layout.menu_contents("DBBM_MT_preset_menu")

@_
class DBBM_PT_presets(PresetPanel,bpy.types.Panel):
    bl_label = "Bookmark Presets"
    preset_subdir = "dbbm_strings"
    preset_operator = "script.execute_preset"
    preset_add_operator = "dbbm.add_preset"


@_
class DBBM_OT_dbbm_preset_add(AddPresetBase,bpy.types.Operator):
    bl_idname = "dbbm.add_preset"
    bl_label = "Bookmark this Datablock"
    preset_menu = "DBBM_MT_preset_menu"
    preset_subdir = "dbbm_strings"
    preset_defines = ["dbbm = bpy.context.window_manager.dbbm"]
    preset_values = ["dbbm.dbbm_string"]


@_
class DBBM_MT_preset_menu(bpy.types.Menu):
    bl_label = "bookmark presets"
    preset_subdir = "dbbm_strings"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


@_
class DBBMPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    default_filepath: bpy.props.StringProperty(
        subtype="DIR_PATH",
        maxlen=1024,
        default=str(pathlib.Path.home()/"Documents"/"Blender"/"Assets"))
    def getlib(self,context):
        try:
            return context.preferences.filepaths.asset_libraries[0].path
        except:
            return self.default_filepath
    def draw(self,context):
        fpathprefs = context.preferences.filepaths
        layout = self.layout
        box = layout.box()
        if not hasattr(context.preferences.filepaths,"asset_libraries"):
            box.prop(self,"default_filepath")
        box.label(text=self.getlib(context))



def get_dbbm(self):
    return self["dbbm_string"]

def set_dbbm(self,dbbm_string):
    self["dbbm_string"] = dbbm_string
    (a,b,c) = dbbm_string.split("|")
    with bpy.data.libraries.load(c) as (df,dt):
        dt.objects = [b]
    ob = dt.objects[0]
    bpy.context.scene.collection.objects.link(ob)
    ob.location = bpy.context.scene.cursor.location
    ob.rotation_euler = bpy.context.region_data.view_rotation.to_euler()


@_
class DbBm(bpy.types.PropertyGroup):
    dbbm_string: bpy.props.StringProperty(set=set_dbbm,get=get_dbbm)


def draw_object_send(self,context):
    self.layout.operator("dbbm.send")

def draw_object_add(self,context):
    self.layout.menu("DBBM_MT_preset_menu")

def hotkey_things(do=False,t=[]):
    if do:
        keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps
        mods = dict(ctrl=True,alt=True,shift=True,oskey=False)
        mtype = "T"
        value = "PRESS"
        if "3D View" not in keymaps:
            km = keymaps.new("3D View",space_type="VIEW_3D")
        else:
            km = keymaps["3D View"]
        kmi = km.keymap_items.new(DBBM_OT_send.bl_idname,
                                  mtype,value,**mods)
        t.append((km,kmi))
    else:
        for km,kmi in t:
            km.keymap_items.remove(kmi)
        t.clear()

def register():
    list(map(bpy.utils.register_class,_()))
    bpy.types.VIEW3D_MT_object.append(draw_object_send)
    bpy.types.VIEW3D_MT_add.append(draw_object_add)
    bpy.types.WindowManager.dbbm = bpy.props.PointerProperty(type=DbBm)
    hotkey_things(do=True)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(draw_object_send)
    bpy.types.VIEW3D_MT_add.remove(draw_object_add)
    del bpy.types.WindowManager.dbbm
    list(map(bpy.utils.unregister_class,_()))
    hotkey_things()

#{{{1
"""
"actions",
"armatures",
"brushes",
"cache_files",
"cameras",
"collections",
"curves",
"fonts",
"grease_pencils",
"hairs",
"images",
"lattices",
"lightprobes",
"lights",
"linestyles",
"masks",
"materials",
"meshes",
"metaballs",
"movieclips",
"node_groups",
"objects",
"paint_curves",
"palettes",
"particles",
"pointclouds",
"scenes",
"screens",
"simulations",
"sounds",
"speakers",
"texts",
"textures",
"volumes",
"workspaces",
"worlds"
"""
