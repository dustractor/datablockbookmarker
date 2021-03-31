bl_info = {
    "name": "Datablock Bookmarker",
    "category": "System",
    "blender": (2,80,0),
    "version": (0,2)}

from pathlib import Path
from bpy.types import (
    Panel,Operator,AddonPreferences,Menu,WindowManager,PropertyGroup)
from bpy.utils import (
    register_class,unregister_class,preset_paths,user_resource)
from bl_operators.presets import AddPresetBase
from bl_ui.utils import PresetPanel
from bpy.props import (
    PointerProperty,BoolProperty,StringProperty)




def _(a=None,b=[]):
    if a:
        b.append(a)
        return a
    else:
        return b


@_
class DBBM_OT_send(Operator):
    bl_idname = "dbbm.send"
    bl_label = "dbbm send"
    overwrite: BoolProperty()
    def invoke(self,context,event):
        context.window_manager.invoke_props_dialog(self)
        return {"RUNNING_MODAL"}
    def execute(self,context):
        prefs = context.preferences.addons[__package__].preferences
        target = prefs.getlib(context)
        targetpath = Path(target)
        import bpy
        for ob in context.selected_editable_objects:
            filepath = targetpath / (ob.type + "_" + bpy.path.clean_name(ob.name) + ".blend")
            if filepath.exists() and not self.overwrite:
                self.report({"WARNING"},"file exists:"+str(filepath))
            bpy.data.libraries.write(
                str(filepath),
                set([ob]),
                fake_user=True)
            context.window_manager.dbbm["dbbm_string"] = "|".join((
                    ob.type,ob.name,str(filepath)))
            print(context.window_manager.dbbm["dbbm_string"])
            bpy.ops.dbbm.add_preset(name=filepath.stem)
            self.report({"INFO"},"file written: " + str(filepath))

        return {"FINISHED"}


@_
class DBBM_PT_bookmarks(Panel):
    bl_label = "DBBM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DBBM"
    def draw_header_preset(self,context):
        DBBM_PT_presets.draw_panel_header(self.layout)
    def draw(self,context):
        layout = self.layout
        fpathprefs = context.preferences.filepaths
        if hasattr(fpathprefs,"asset_libraries"):
            lib = fpathprefs.asset_libraries[0].path
        else:
            prefs = context.preferences.addons[__package__].preferences
            lib = prefs.default_filepath
        layout.label(text=lib)
        libp = Path(lib)
        for f in libp.glob("*.blend"):
            layout.label(text=f.stem,icon="FILE_BLEND")
@_
class DBBM_PT_presets(PresetPanel,Panel):
    bl_label = "Bookmark Presets"
    preset_subdir = "dbbm_strings"
    preset_operator = "script.execute_preset"
    preset_add_operator = "dbbm.add_preset"
@_
class DBBM_OT_dbbm_preset_add(AddPresetBase,Operator):
    bl_idname = "dbbm.add_preset"
    bl_label = "Bookmark this Datablock"
    preset_menu = "DBBM_MT_preset_menu"
    preset_subdir = "dbbm_strings"
    preset_defines = ["dbbm = bpy.context.window_manager.dbbm"]
    preset_values = ["dbbm.dbbm_string"]

@_
class DBBM_MT_preset_menu(Menu):
    bl_label = "bookmark presets"
    preset_subdir = "dbbm_strings"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset

@_
class DBBMPreferences(AddonPreferences):
    bl_idname = __package__
    default_filepath: StringProperty(
        subtype="DIR_PATH",
        maxlen=1024,
        default=str(Path.home()/"Documents"/"Blender"/"Assets"))
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

def hotkey_things(do=False,t=[]):
    import bpy
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
def get_dbbm(self):
    print("self:",self)
    return self["dbbm_string"]
def set_dbbm(self,dbbm_string):
    self["dbbm_string"] = dbbm_string
    (a,b,c) = dbbm_string.split("|")
    print("a,b,c:",a,b,c)
    import bpy
    with bpy.data.libraries.load(c) as (df,dt):
        dt.objects = [b]
        print("dir(dt):",dir(dt))
    ob = dt.objects[0]
    bpy.context.scene.collection.objects.link(ob)
    print("OK")
    """
    ["actions",
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
    "worlds"]
    """

@_
class DbBm(PropertyGroup):
    dbbm_string: StringProperty(set=set_dbbm,get=get_dbbm)

def register():
    list(map(register_class,_()))
    WindowManager.dbbm = PointerProperty(type=DbBm)
    hotkey_things(do=True)

def unregister():
    del WindowManager.dbbm
    list(map(unregister_class,_()))
    hotkey_things()

