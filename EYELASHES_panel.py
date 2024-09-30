bl_info = {
    "name": "EyelashesGenerate",
    "author": "bardelfs",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Object > EyeLashes Generate",
    "description": "Generate eyelashes from template",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
import random
from bpy.props import FloatProperty, IntProperty

# Определение пользовательских свойств сцены
bpy.types.Scene.RotateStartX = FloatProperty(
    name="Rotate Start X",
    description="RotateStartX value",
    default=-0.1,
    min=-1,
    max=0
)
bpy.types.Scene.RotateEndX = FloatProperty(
    name="Rotate End X",
    description="RotateEndX value",
    default=0.1,
    min=0,
    max=1
)
bpy.types.Scene.RotateStartY = FloatProperty(
    name="Rotate Start Y",
    description="RotateStartY value",
    default=-0.05,
    min=-1,
    max=0
)
bpy.types.Scene.RotateEndY = FloatProperty(
    name="Rotate End Y",
    description="RotateEndY value",
    default=0.05,
    min=0,
    max=1
)
bpy.types.Scene.RotateStartZ = FloatProperty(
    name="Rotate Start Z",
    description="RotateStartZ value",
    default=-0.1,
    min=-1,
    max=0
)
bpy.types.Scene.RotateEndZ = FloatProperty(
    name="Rotate End Z",
    description="RotateEndZ value",
    default=0.1,
    min=0,
    max=1
)
bpy.types.Scene.ScaleEnd = FloatProperty(
    name="Scale End",
    description="ScaleEnd value",
    default=0.1,
    min=0,
    max=1
)
bpy.types.Scene.ScaleStart = FloatProperty(
    name="Scale Start",
    description="ScaleStart value",
    default=-0.1,
    min=-1,
    max=0
)
bpy.types.Scene.PosStart = FloatProperty(
    name="Pos Start",
    description="PosStart value",
    default=0,
    min=-1,
    max=0
)
bpy.types.Scene.PosEnd = FloatProperty(
    name="Pos End",
    description="PosEnd value",
    default=0,
    min=0,
    max=1
)
bpy.types.Scene.RateGen = IntProperty(
    name="RateGen",
    description="RateGen value",
    default=1,
    min=1,
    max=1000
)
bpy.types.Scene.MaxFrame = IntProperty(
    name="MaxFrame",
    description="MaxFrame value",
    default=100,
    min=1,
    max=100000
)

def main(context):
    obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else None
    if not obj:
        self.report({'ERROR'}, "No object selected")
        return
    
    print(f"Selected object: {obj.name}")

    def stop_playback(scene):
        # Выполняем операцию каждые `RateGen` кадров
        if scene.frame_current % scene.RateGen == 0:
            print(f"Duplicating object at frame {scene.frame_current}")
            # Дублируем объект, убедившись, что контекст корректный
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')  # Снимем выделение со всех объектов
            obj.select_set(True)  # Выделим исходный объект
            bpy.ops.object.duplicate(linked=False)
            new_obj = bpy.context.view_layer.objects.active  # Новый объект становится активным
            
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # Убедимся, что объект дублирован
            print(f"New object duplicated: {new_obj.name}")

            # Очищаем анимацию у нового объекта и применяем случайные трансформации
            new_obj.animation_data_clear()

            new_obj.rotation_euler[0] += random.uniform(scene.RotateStartX, scene.RotateEndX)
            new_obj.rotation_euler[1] += random.uniform(scene.RotateStartY, scene.RotateEndY)
            new_obj.rotation_euler[2] += random.uniform(scene.RotateStartZ, scene.RotateEndZ) + (
                        (scene.frame_current - scene.MaxFrame / 2) * 0.01)
            new_obj.scale[0] += random.uniform(scene.ScaleStart, scene.ScaleEnd)
            new_obj.scale[1] += random.uniform(scene.ScaleStart, scene.ScaleEnd)
            new_obj.scale[2] += random.uniform(scene.ScaleStart, scene.ScaleEnd)
            new_obj.location[2] += random.uniform(scene.PosStart, scene.PosEnd)

            bpy.ops.object.select_all(action='DESELECT')  # Снимем выделение со всех объектов
        # Останавливаем анимацию на последнем кадре
        if scene.frame_current >= scene.MaxFrame:
            print(f"Stopping playback at frame {scene.frame_current}")
            bpy.ops.screen.animation_cancel(restore_frame=True)
            if stop_playback in bpy.app.handlers.frame_change_pre:
                bpy.app.handlers.frame_change_pre.remove(stop_playback)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    if stop_playback not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(stop_playback)
    
    bpy.ops.screen.animation_play()

# Оператор, запускающий процесс создания ресниц
class EyelashesOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.eyelashes_operator"
    bl_label = "Eyelashes Create"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}

# Панель для настройки параметров
class EyelashesPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "EyeLashes Generate"
    bl_idname = "EYE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
    

        # Create a simple row.
        layout.label(text="Random Rotate Interval")

        row = layout.row()
        row.prop(scene, "RotateStartX")
        row.prop(scene, "RotateEndX")
        row = layout.row()
        row.prop(scene, "RotateStartY")
        row.prop(scene, "RotateEndY")
        row = layout.row()
        row.prop(scene, "RotateStartZ")
        row.prop(scene, "RotateEndZ")
        #row.prop(R_X, "endX")
        
        layout.label(text="Random Scale Interval")
        row = layout.row()
        row.prop(scene, "ScaleStart")
        row.prop(scene, "ScaleEnd")
        layout.label(text="Random Position Interval")
        row = layout.row()
        row.prop(scene, "PosStart")
        row.prop(scene, "PosEnd")
        
        layout.label(text="Rate Generation")
        row = layout.row()
        row.prop(scene, "RateGen")
        layout.label(text="Max Frame")
        row = layout.row()
        row.prop(scene, "MaxFrame")
        # Big render button
        layout.label(text="Generate")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.eyelashes_operator")
# Регистрация классов
def register():
    bpy.utils.register_class(EyelashesPanel)
    bpy.utils.register_class(EyelashesOperator)

# Unregister function
def unregister():
    bpy.utils.unregister_class(EyelashesPanel)
    bpy.utils.unregister_class(EyelashesOperator)
    if stop_playback in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(stop_playback)

if __name__ == "__main__":
    register()