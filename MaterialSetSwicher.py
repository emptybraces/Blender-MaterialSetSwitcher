bl_info = {
    "name": "Material Set Switcher",
    "author": "emptybraces",
    "version": (1, 0),
    "blender": (3, 6, 2),
    "location": "View3D -> Tool",
    "description": "Quickly replace material slots.",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Misc",
}

import bpy
from bl_ui.generic_ui_list import draw_ui_list

def update_category(self, context):
    new_cate = MSS_MT_AddonPreferences.get_ref().category
    if new_cate != "":
        bpy.utils.unregister_class(MSS_PT_Panel)
        MSS_PT_Panel.bl_category = new_cate
        bpy.utils.register_class(MSS_PT_Panel)

class MSS_MT_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    category: bpy.props.StringProperty(name="Category", default="Misc", update = update_category)
    def draw(self, context):
        layout = self.layout.box()
        layout.prop(self, "category")
    @staticmethod
    def get_ref(): 
        return bpy.context.preferences.addons[__name__].preferences

class MSS_PropGroupData(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    
class MSS_PropGroupSetDataList(bpy.types.PropertyGroup):
    dataList: bpy.props.CollectionProperty(type=MSS_PropGroupData)
    def FillByDefaultMaterialSlot(self, obj):
        self.name = "default"
        self.dataList.clear()
        for i in obj.material_slots:
            data = self.dataList.add()
            data.name = i.name

class MSS_OT_ApplyMaterialSlot(bpy.types.Operator):
    bl_idname = "mss.apply_mat_slot"
    bl_label = "Apply"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.active_object
        data_list = obj.mss_set_list[obj.mss_list_active_idx].dataList
        obj.data.materials.clear()
        for i in data_list:
            mat = bpy.data.materials.get(i.name)
            obj.data.materials.append(mat)
        return {'FINISHED'}

class MSS_OT_SlotListSideMenu(bpy.types.Operator):
    bl_idname = "mss.slotlist_side_menu"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}
    optionId: bpy.props.StringProperty()
    def execute(self, context):
        obj = context.active_object
        data_list = obj.mss_set_list[obj.mss_list_active_idx].dataList
        if self.optionId == "add":
            data = data_list.add()
            data.name = "none"
        elif self.optionId == "remove":
            data = data_list.remove(obj.mss_data_active_idx)
            if obj.mss_data_active_idx != 0:
               obj.mss_data_active_idx -= 1
        elif self.optionId == "up":
            data_list.move(obj.mss_data_active_idx, obj.mss_data_active_idx - 1)
        elif self.optionId == "down":
            data_list.move(obj.mss_data_active_idx, obj.mss_data_active_idx + 1)
            for i in obj.mss_set_list:
                print(i.name)
                if len(i.dataList) == 0:
                    i.name = "default"
                    i.FillByDefaultMaterialSlot(obj)
        return {'FINISHED'}

class MSS_OT_SetListSideMenu(bpy.types.Operator):
    bl_idname = "mss.setlist_side_menu"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}
    optionId: bpy.props.StringProperty()
    def execute(self, context):
        obj = context.active_object
        data_list = obj.mss_set_list
        if self.optionId == "add":
            data = data_list.add()
            data.FillByDefaultMaterialSlot(obj)
            obj.mss_list_active_idx = len(data_list) - 1
        elif self.optionId == "remove":
            data = data_list.remove(obj.mss_list_active_idx)
            if obj.mss_list_active_idx != 0:
               obj.mss_list_active_idx -= 1
        elif self.optionId == "up":
            data_list.move(obj.mss_list_active_idx, obj.mss_list_active_idx - 1)
        elif self.optionId == "down":
            data_list.move(obj.mss_list_active_idx, obj.mss_list_active_idx + 1)
        return {'FINISHED'}

class MSS_UL_SlotList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        idx = 0
        for i in range(len(data.dataList)):
            if data.dataList[i] == item:
                idx = i
                break
        # print(data, item, active_data, active_propname)
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # layout.prop_search(item, "name", bpy.data, "materials", text=f"{i}")
            layout.prop_search(item, "name", bpy.data, "materials", text=f"{i}")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class MSS_PT_Panel(bpy.types.Panel):
    bl_label = "Material Set Switcher"
    bl_idname = "MSS_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Misc"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj == None:
            layout.label(text="No object is selected.")
            return
        row = layout.row()
        col = row.column()
        draw_ui_list(
            col,
            context,
            list_path="object.mss_set_list",
            active_index_path="object.mss_list_active_idx",
            unique_id="mss_set_list_id",
            insertion_operators=False,
            move_operators=False
        )
        col.operator(MSS_OT_ApplyMaterialSlot.bl_idname)
        col = row.column()
        col.operator(MSS_OT_SetListSideMenu.bl_idname, icon='ADD', text="").optionId = "add"
        col.operator(MSS_OT_SetListSideMenu.bl_idname, icon='REMOVE', text="").optionId = "remove"
        col.operator(MSS_OT_SetListSideMenu.bl_idname, icon='TRIA_UP', text="").optionId = "up"
        col.operator(MSS_OT_SetListSideMenu.bl_idname, icon='TRIA_DOWN', text="").optionId = "down"
        # print("mss_set_list size is", len(obj.mss_set_list))
        if 0 < len(obj.mss_set_list):
            row.template_list("MSS_UL_SlotList", "", obj.mss_set_list[obj.mss_list_active_idx], "dataList", obj, "mss_data_active_idx")
            col = row.column()
            col.operator(MSS_OT_SlotListSideMenu.bl_idname, icon='ADD', text="").optionId = "add"
            col.operator(MSS_OT_SlotListSideMenu.bl_idname, icon='REMOVE', text="").optionId = "remove"
            col.operator(MSS_OT_SlotListSideMenu.bl_idname, icon='TRIA_UP', text="").optionId = "up"
            col.operator(MSS_OT_SlotListSideMenu.bl_idname, icon='TRIA_DOWN', text="").optionId = "down"

classes = [
    MSS_MT_AddonPreferences,
    MSS_PropGroupData,
    MSS_PropGroupSetDataList,
    MSS_UL_SlotList,
    MSS_PT_Panel,
    MSS_OT_SlotListSideMenu,
    MSS_OT_SetListSideMenu,
    MSS_OT_ApplyMaterialSlot,
]

class_register, class_unregister = bpy.utils.register_classes_factory(classes)

def register():
    class_register()
    bpy.types.Object.mss_set_list = bpy.props.CollectionProperty(type=MSS_PropGroupSetDataList)
    bpy.types.Object.mss_list_active_idx = bpy.props.IntProperty()
    bpy.types.Object.mss_data_active_idx = bpy.props.IntProperty()

def unregister():
    class_unregister()
    del bpy.types.Object.mss_set_list
    del bpy.types.Object.mss_list_active_idx
    del bpy.types.Object.mss_data_active_idx

if __name__ == "__main__":
    register()