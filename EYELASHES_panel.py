bl_info = {
    "name": "EyelashesGenerate",
    "author": "bardelfs",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "Properties > Object > EyeLashes Generate",
    "description": "Generate eyelashes from template (frame-stepping, undo-safe)",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
import random
from bpy.props import FloatProperty, IntProperty


# ---------- Scene props (как в оригинале) ----------
def ensure_scene_props():
    S = bpy.types.Scene
    if not hasattr(S, "RotateStartX"):
        S.RotateStartX = FloatProperty(name="Rotate Start X", description="RotateStartX value", default=-0.1, min=-1, max=0)
        S.RotateEndX   = FloatProperty(name="Rotate End X",   description="RotateEndX value", default= 0.1, min= 0, max=1)
        S.RotateStartY = FloatProperty(name="Rotate Start Y", description="RotateStartY value", default=-0.05, min=-1, max=0)
        S.RotateEndY   = FloatProperty(name="Rotate End Y",   description="RotateEndY value", default= 0.05, min= 0, max=1)
        S.RotateStartZ = FloatProperty(name="Rotate Start Z", description="RotateStartZ value", default=-0.1, min=-1, max=0)
        S.RotateEndZ   = FloatProperty(name="Rotate End Z",   description="RotateEndZ value", default= 0.1, min= 0, max=1)
        S.ScaleEnd     = FloatProperty(name="Scale End",      description="ScaleEnd value",   default= 0.1, min= 0, max=1)
        S.ScaleStart   = FloatProperty(name="Scale Start",    description="ScaleStart value", default=-0.1, min=-1, max=0)
        S.PosStart     = FloatProperty(name="Pos Start",      description="PosStart value", default=0, min=-1, max=0)
        S.PosEnd       = FloatProperty(name="Pos End",        description="PosEnd value",   default=0, min=0, max=1)
        S.RateGen      = IntProperty  (name="RateGen",        description="Duplicate every N frames", default=1, min=1, max=1000)
        S.MaxFrame     = IntProperty  (name="MaxFrame",       description="Last frame to reach",       default=100, min=1, max=100000)

ensure_scene_props()


# ---------- Дублирование через data-API ----------
def duplicate_object_datablock(src_obj: bpy.types.Object) -> bpy.types.Object:
    """Создать независимую копию объекта и его data, залинковать в те же коллекции."""
    new_obj = src_obj.copy()
    if src_obj.data:
        new_obj.data = src_obj.data.copy()
    if src_obj.users_collection:
        for col in src_obj.users_collection:
            col.objects.link(new_obj)
    else:
        bpy.context.scene.collection.objects.link(new_obj)
    # Чистим анимацию у копии
    if new_obj.animation_data:
        new_obj.animation_data_clear()
    new_obj.parent = None
    new_obj.matrix_parent_inverse.identity()
    return new_obj


# ---------- Оператор: шаг по кадрам и спавн копий ----------
class EyelashesOperator(bpy.types.Operator):
    """Spawn duplicates along the animated motion of the source; copies keep pose, no animation."""
    bl_idname = "object.eyelashes_operator"
    bl_label = "Eyelashes Create"
    bl_options = {'REGISTER', 'UNDO', 'UNDO_GROUPED'}

    _timer = None
    _source_name = None
    _start_frame = 0
    _target_last = 0
    _spawned = 0

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # на случай вызова не через кнопку — перейти в invoke
        return self.invoke(context, None)

    def invoke(self, context, event):
        src = context.active_object
        if not src:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}

        scn = context.scene
        self._source_name = src.name
        self._start_frame = scn.frame_current
        self._target_last = scn.MaxFrame
        self._spawned = 0

        # таймер для модального цикла
        wm = context.window_manager
        win = context.window or bpy.context.window
        if win is None:
            self.report({'ERROR'}, "No active window found for timer")
            return {'CANCELLED'}
        self._timer = wm.event_timer_add(0.0, window=win)  # 0.0 = тики по возможности
        wm.modal_handler_add(self)

        print(f"[Eyelashes] Start: src={self._source_name}, start={self._start_frame}, end={self._target_last}")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            print(f"[Eyelashes] Cancelled. Spawned={self._spawned}")
            return self._finish(context, restore_frame=True, cancelled=True)

        if event.type == 'TIMER':
            scn = context.scene
            cur = scn.frame_current

            # Дублируем на каждом кратном RateGen кадре
            if (cur - self._start_frame) % max(1, scn.RateGen) == 0:
                src = bpy.data.objects.get(self._source_name)
                if src is None:
                    self.report({'WARNING'}, "Source object disappeared. Stopping.")
                    return self._finish(context, restore_frame=True)

                # Важно: берем позу из evaluated depsgraph на текущем кадре
                depsgraph = context.evaluated_depsgraph_get()
                src_eval = src.evaluated_get(depsgraph)
                world_mx = src_eval.matrix_world.copy()

                new_obj = duplicate_object_datablock(src)
                # ставим в ту же мировую позу, что у оригинала на этом кадре
                new_obj.matrix_world = world_mx

                # Рандом-трансформации (как в исходнике)
                new_obj.rotation_euler[0] += random.uniform(scn.RotateStartX, scn.RotateEndX)
                new_obj.rotation_euler[1] += random.uniform(scn.RotateStartY, scn.RotateEndY)
                new_obj.rotation_euler[2] += random.uniform(scn.RotateStartZ, scn.RotateEndZ) + (
                    (cur - scn.MaxFrame / 2) * 0.01
                )
                new_obj.scale[0] += random.uniform(scn.ScaleStart, scn.ScaleEnd)
                new_obj.scale[1] += random.uniform(scn.ScaleStart, scn.ScaleEnd)
                new_obj.scale[2] += random.uniform(scn.ScaleStart, scn.ScaleEnd)
                new_obj.location[2] += random.uniform(scn.PosStart, scn.PosEnd)

                self._spawned += 1
                print(f"[Eyelashes] Frame {cur}: duplicated -> {new_obj.name} (total {self._spawned})")

            # Переходим на следующий кадр
            if cur >= self._target_last:
                print(f"[Eyelashes] Reached end={self._target_last}. Spawned={self._spawned}")
                return self._finish(context, restore_frame=True)

            scn.frame_set(cur + 1)  # собственно движение по таймлайну

        return {'RUNNING_MODAL'}

    def _finish(self, context, restore_frame=True, cancelled=False):
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None
        if restore_frame:
            try:
                context.scene.frame_set(self._start_frame)
            except Exception:
                pass
        return {'CANCELLED' if cancelled else 'FINISHED'}


# ---------- Панель UI (как у тебя) ----------
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

        layout.label(text="Random Rotate Interval")
        row = layout.row()
        row.prop(scene, "RotateStartX"); row.prop(scene, "RotateEndX")
        row = layout.row()
        row.prop(scene, "RotateStartY"); row.prop(scene, "RotateEndY")
        row = layout.row()
        row.prop(scene, "RotateStartZ"); row.prop(scene, "RotateEndZ")

        layout.label(text="Random Scale Interval")
        row = layout.row()
        row.prop(scene, "ScaleStart"); row.prop(scene, "ScaleEnd")

        layout.label(text="Random Position Interval")
        row = layout.row()
        row.prop(scene, "PosStart"); row.prop(scene, "PosEnd")

        layout.label(text="Rate Generation")
        row = layout.row()
        row.prop(scene, "RateGen")

        layout.label(text="Max Frame")
        row = layout.row()
        row.prop(scene, "MaxFrame")

        layout.separator()
        layout.label(text="Generate along animation")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.eyelashes_operator")


# ---------- Регистрация ----------
classes = (EyelashesPanel, EyelashesOperator)

def register():
    ensure_scene_props()
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
