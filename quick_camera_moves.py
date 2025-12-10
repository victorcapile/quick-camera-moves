bl_info = {
    "name": "Quick Camera Moves",
    "author": "Victor Capilé",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Camera Moves",
    "description": "Cria movimentos cinematográficos de câmera com poucos cliques",
    "category": "Animation",
}

import bpy
import math
from mathutils import Vector
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    BoolProperty,
)


# ============================================================
# PROPERTIES
# ============================================================

class QCM_Properties(bpy.types.PropertyGroup):
    move_type: EnumProperty(
        name="Movimento",
        description="Tipo de movimento da câmera",
        items=[
            ('ORBIT', "Orbit", "Gira ao redor do target"),
            ('DOLLY_IN', "Dolly In", "Aproxima do target"),
            ('DOLLY_OUT', "Dolly Out", "Afasta do target"),
            ('TRUCK_LEFT', "Truck Left", "Move para esquerda"),
            ('TRUCK_RIGHT', "Truck Right", "Move para direita"),
            ('PEDESTAL_UP', "Pedestal Up", "Sobe a câmera"),
            ('PEDESTAL_DOWN', "Pedestal Down", "Desce a câmera"),
            ('CRANE', "Crane Shot", "Arco de cima para baixo"),
        ],
        default='ORBIT'
    )
    
    duration: FloatProperty(
        name="Duração",
        description="Duração do movimento em segundos",
        default=2.0,
        min=0.5,
        max=30.0,
        unit='TIME'
    )
    
    orbit_angle: FloatProperty(
        name="Ângulo",
        description="Ângulo de rotação (para Orbit)",
        default=360.0,
        min=-720.0,
        max=720.0,
        subtype='ANGLE'
    )
    
    move_distance: FloatProperty(
        name="Distância",
        description="Distância do movimento",
        default=5.0,
        min=0.1,
        max=100.0,
        unit='LENGTH'
    )
    
    use_easing: BoolProperty(
        name="Easing Suave",
        description="Aplica ease in/out na animação",
        default=True
    )
    
    keep_target_focus: BoolProperty(
        name="Manter Foco no Target",
        description="Câmera sempre olha para o target",
        default=True
    )


# ============================================================
# AUX FUNCTIONS
# ============================================================

def get_active_camera(context):
    if context.scene.camera:
        return context.scene.camera
    return None


def get_target_location(context):
    if context.active_object and context.active_object.type != 'CAMERA':
        return context.active_object.location.copy()
    return context.scene.cursor.location.copy()


def set_keyframe_interpolation(obj, easing=True):
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if easing:
                    keyframe.interpolation = 'BEZIER'
                    keyframe.easing = 'EASE_IN_OUT'
                else:
                    keyframe.interpolation = 'LINEAR'


def add_track_constraint(camera, target_obj=None, target_loc=None):
    for c in camera.constraints:
        if c.name == "QCM_Track":
            camera.constraints.remove(c)
    
    if target_obj:
        constraint = camera.constraints.new('TRACK_TO')
        constraint.name = "QCM_Track"
        constraint.target = target_obj
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
    elif target_loc:
        bpy.ops.object.empty_add(location=target_loc)
        empty = bpy.context.active_object
        empty.name = "QCM_Target"
        
        constraint = camera.constraints.new('TRACK_TO')
        constraint.name = "QCM_Track"
        constraint.target = empty
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
        return empty
    return None


# ============================================================
# OPERATORS
# ============================================================

class QCM_OT_create_move(bpy.types.Operator):
    bl_idname = "qcm.create_move"
    bl_label = "Criar Movimento"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.qcm_props
        camera = get_active_camera(context)
        
        if not camera:
            self.report({'ERROR'}, "Nenhuma câmera ativa na cena")
            return {'CANCELLED'}
        
        fps = context.scene.render.fps
        start_frame = context.scene.frame_current
        end_frame = start_frame + int(props.duration * fps)
        
        target_obj = None
        if context.active_object and context.active_object != camera:
            target_obj = context.active_object
        target_loc = get_target_location(context)
        
        move_type = props.move_type
        
        if move_type == 'ORBIT':
            self.create_orbit(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('DOLLY_IN', 'DOLLY_OUT'):
            self.create_dolly(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('TRUCK_LEFT', 'TRUCK_RIGHT'):
            self.create_truck(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('PEDESTAL_UP', 'PEDESTAL_DOWN'):
            self.create_pedestal(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type == 'CRANE':
            self.create_crane(context, camera, target_loc, start_frame, end_frame, props)
        
        set_keyframe_interpolation(camera, props.use_easing)
        
        context.scene.frame_end = max(context.scene.frame_end, end_frame)
        
        self.report({'INFO'}, f"Movimento '{move_type}' criado: frames {start_frame}-{end_frame}")
        return {'FINISHED'}
    
    def create_orbit(self, context, camera, target_loc, start_frame, end_frame, props):
        offset = camera.location - target_loc
        radius = offset.length
        start_angle = math.atan2(offset.y, offset.x)
        
        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        
        total_angle = math.radians(props.orbit_angle)
        steps = max(4, int(abs(props.orbit_angle) / 45))
        
        for i in range(1, steps + 1):
            progress = i / steps
            frame = start_frame + int((end_frame - start_frame) * progress)
            angle = start_angle + (total_angle * progress)
            
            new_x = target_loc.x + radius * math.cos(angle)
            new_y = target_loc.y + radius * math.sin(angle)
            
            camera.location.x = new_x
            camera.location.y = new_y
            camera.keyframe_insert(data_path="location", frame=frame)
        
        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)
    
    def create_dolly(self, context, camera, target_loc, start_frame, end_frame, props):
        direction = (target_loc - camera.location).normalized()
        
        if props.move_type == 'DOLLY_OUT':
            direction = -direction
        
        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        
        camera.location += direction * props.move_distance
        camera.keyframe_insert(data_path="location", frame=end_frame)
        
        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)
    
    def create_truck(self, context, camera, target_loc, start_frame, end_frame, props):
        forward = (target_loc - camera.location).normalized()
        up = Vector((0, 0, 1))
        right = forward.cross(up).normalized()
        
        if props.move_type == 'TRUCK_LEFT':
            right = -right
        
        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        
        camera.location += right * props.move_distance
        camera.keyframe_insert(data_path="location", frame=end_frame)
        
        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)
    
    def create_pedestal(self, context, camera, target_loc, start_frame, end_frame, props):
        direction = Vector((0, 0, 1))
        
        if props.move_type == 'PEDESTAL_DOWN':
            direction = -direction
        
        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        
        camera.location += direction * props.move_distance
        camera.keyframe_insert(data_path="location", frame=end_frame)
        
        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)
    
    def create_crane(self, context, camera, target_loc, start_frame, end_frame, props):
        offset = camera.location - target_loc
        radius = offset.length
        
        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        
        steps = 8
        for i in range(1, steps + 1):
            progress = i / steps
            frame = start_frame + int((end_frame - start_frame) * progress)
            
            angle = math.radians(90 * progress)
            
            horizontal_dist = radius * math.cos(math.radians(45) - angle * 0.5)
            height = radius * math.sin(math.radians(90) - angle)
            
            direction_2d = Vector((offset.x, offset.y, 0)).normalized()
            
            camera.location.x = target_loc.x + direction_2d.x * horizontal_dist
            camera.location.y = target_loc.y + direction_2d.y * horizontal_dist
            camera.location.z = target_loc.z + height
            
            camera.keyframe_insert(data_path="location", frame=frame)
        
        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)


class QCM_OT_clear_animation(bpy.types.Operator):
    bl_idname = "qcm.clear_animation"
    bl_label = "Limpar Animação"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        camera = get_active_camera(context)
        
        if not camera:
            self.report({'ERROR'}, "Nenhuma câmera ativa")
            return {'CANCELLED'}
        
        camera.animation_data_clear()
        
        for c in camera.constraints:
            if c.name.startswith("QCM_"):
                camera.constraints.remove(c)
        
        for obj in bpy.data.objects:
            if obj.name.startswith("QCM_Target"):
                bpy.data.objects.remove(obj, do_unlink=True)
        
        self.report({'INFO'}, "Animação da câmera removida")
        return {'FINISHED'}


class QCM_OT_preview(bpy.types.Operator):
    bl_idname = "qcm.preview"
    bl_label = "Preview"
    
    def execute(self, context):
        bpy.ops.screen.animation_play()
        return {'FINISHED'}


# ============================================================
# UI PANEL
# ============================================================

class QCM_PT_main_panel(bpy.types.Panel):
    bl_label = "Quick Camera Moves"
    bl_idname = "QCM_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Moves"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.qcm_props
        camera = get_active_camera(context)
        
        box = layout.box()
        if camera:
            box.label(text=f"Câmera: {camera.name}", icon='CAMERA_DATA')
        else:
            box.label(text="Sem câmera ativa!", icon='ERROR')
        
        if context.active_object and context.active_object != camera:
            box.label(text=f"Target: {context.active_object.name}", icon='OBJECT_DATA')
        else:
            box.label(text="Target: 3D Cursor", icon='CURSOR')
        
        layout.separator()
        
        layout.prop(props, "move_type")
        layout.prop(props, "duration")
        
        if props.move_type == 'ORBIT':
            layout.prop(props, "orbit_angle")
        else:
            layout.prop(props, "move_distance")
        
        layout.separator()
        
        layout.prop(props, "use_easing")
        layout.prop(props, "keep_target_focus")
        
        layout.separator()
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("qcm.create_move", icon='PLAY')
        
        row = layout.row(align=True)
        row.operator("qcm.preview", icon='PREVIEW_RANGE')
        row.operator("qcm.clear_animation", icon='X')


# ============================================================
# REGISTER
# ============================================================

classes = (
    QCM_Properties,
    QCM_OT_create_move,
    QCM_OT_clear_animation,
    QCM_OT_preview,
    QCM_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.qcm_props = PointerProperty(type=QCM_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.qcm_props


if __name__ == "__main__":
    register()
