bl_info = {
    "name": "Quick Camera Moves",
    "author": "Victor",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Camera Moves",
    "description": "Cria movimentos cinematográficos de câmera com poucos cliques",
    "category": "Animation",
}

import bpy
import math
import random
from mathutils import Vector, Euler
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    BoolProperty,
)


# ============================================================
# PROPRIEDADES
# ============================================================

class QCM_Properties(bpy.types.PropertyGroup):

    move_type: EnumProperty(
        name="Movimento",
        description="Tipo de movimento da câmera",
        items=[
            ('NONE', "— Selecione —", ""),
            ('HEADER_BASIC', "── Básicos ──", ""),
            ('ORBIT', "Orbit", "Gira ao redor do target"),
            ('DOLLY_IN', "Dolly In", "Aproxima do target"),
            ('DOLLY_OUT', "Dolly Out", "Afasta do target"),
            ('TRUCK_LEFT', "Truck Left", "Move para esquerda"),
            ('TRUCK_RIGHT', "Truck Right", "Move para direita"),
            ('PEDESTAL_UP', "Pedestal Up", "Sobe a câmera"),
            ('PEDESTAL_DOWN', "Pedestal Down", "Desce a câmera"),
            ('HEADER_CINE', "── Cinematográficos ──", ""),
            ('CRANE', "Crane Shot", "Arco de cima para baixo"),
            ('DOLLY_ZOOM', "Dolly Zoom (Vertigo)", "Efeito Hitchcock - fundo distorce"),
            ('ARC_SHOT', "Arc Shot", "Arco 3D ao redor do target"),
            ('WHIP_PAN', "Whip Pan", "Rotação rápida horizontal"),
            ('PUSH_TILT', "Push In + Tilt", "Aproxima com rotação"),
            ('HEADER_PRODUCT', "── Produto/Archviz ──", ""),
            ('TURNTABLE', "Turntable", "Rotação 360° perfeita"),
            ('FLYTHROUGH', "Flythrough", "Atravessa a cena em linha reta"),
            ('ZOOM_IN', "Zoom In", "Aumenta FOV sem mover"),
            ('ZOOM_OUT', "Zoom Out", "Diminui FOV sem mover"),
            ('HEADER_EXTRA', "── Efeitos ──", ""),
            ('SHAKE', "Camera Shake", "Tremida de câmera na mão"),
            ('FOLLOW_PATH', "Follow Path", "Segue curva existente"),
            ('RACK_FOCUS', "Rack Focus Setup", "Prepara mudança de foco"),
        ],
        default='NONE'
    )

    duration: FloatProperty(
        name="Duração",
        description="Duração do movimento em segundos",
        default=2.0,
        min=0.1,
        max=60.0,
        unit='TIME'
    )

    orbit_angle: FloatProperty(
        name="Ângulo",
        description="Ângulo de rotação",
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

    # Dolly Zoom
    dolly_zoom_intensity: FloatProperty(
        name="Intensidade",
        description="Intensidade do efeito Vertigo",
        default=1.0,
        min=0.1,
        max=3.0
    )

    # Shake
    shake_intensity: FloatProperty(
        name="Intensidade",
        description="Intensidade da tremida",
        default=0.5,
        min=0.1,
        max=2.0
    )

    shake_frequency: FloatProperty(
        name="Frequência",
        description="Velocidade da tremida",
        default=2.0,
        min=0.5,
        max=10.0
    )

    # Arc Shot
    arc_height: FloatProperty(
        name="Altura do Arco",
        description="Variação de altura durante o arco",
        default=2.0,
        min=0.0,
        max=20.0,
        unit='LENGTH'
    )

    # Tilt
    tilt_angle: FloatProperty(
        name="Ângulo Tilt",
        description="Ângulo de inclinação vertical",
        default=15.0,
        min=-90.0,
        max=90.0,
        subtype='ANGLE'
    )

    # Zoom
    zoom_fov_start: FloatProperty(
        name="FOV Inicial",
        description="Campo de visão inicial",
        default=50.0,
        min=1.0,
        max=180.0
    )

    zoom_fov_end: FloatProperty(
        name="FOV Final",
        description="Campo de visão final",
        default=20.0,
        min=1.0,
        max=180.0
    )

    # Rack Focus
    rack_focus_start: FloatProperty(
        name="Foco Inicial",
        description="Distância focal inicial",
        default=2.0,
        min=0.1,
        max=100.0,
        unit='LENGTH'
    )

    rack_focus_end: FloatProperty(
        name="Foco Final",
        description="Distância focal final",
        default=10.0,
        min=0.1,
        max=100.0,
        unit='LENGTH'
    )


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_active_camera(context):
    if context.scene.camera:
        return context.scene.camera
    return None


def get_target_location(context):
    if context.active_object and context.active_object.type != 'CAMERA':
        return context.active_object.location.copy()
    return context.scene.cursor.location.copy()


def set_keyframe_interpolation(obj, easing=True, fcurves=None):
    if obj.animation_data and obj.animation_data.action:
        curves = fcurves if fcurves else obj.animation_data.action.fcurves
        for fcurve in curves:
            for keyframe in fcurve.keyframe_points:
                if easing:
                    keyframe.interpolation = 'BEZIER'
                    keyframe.easing = 'EASE_IN_OUT'
                else:
                    keyframe.interpolation = 'LINEAR'


def set_keyframe_interpolation_camera_data(camera, easing=True):
    cam_data = camera.data
    if cam_data.animation_data and cam_data.animation_data.action:
        for fcurve in cam_data.animation_data.action.fcurves:
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
        empty.hide_viewport = True

        constraint = camera.constraints.new('TRACK_TO')
        constraint.name = "QCM_Track"
        constraint.target = empty
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        return empty
    return None


def remove_qcm_objects():
    for obj in bpy.data.objects:
        if obj.name.startswith("QCM_"):
            bpy.data.objects.remove(obj, do_unlink=True)


# ============================================================
# OPERADOR PRINCIPAL
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

        if props.move_type in ('NONE', 'HEADER_BASIC', 'HEADER_CINE', 'HEADER_PRODUCT', 'HEADER_EXTRA'):
            self.report({'WARNING'}, "Selecione um tipo de movimento")
            return {'CANCELLED'}

        # Calcula frames
        fps = context.scene.render.fps
        start_frame = context.scene.frame_current
        end_frame = start_frame + int(props.duration * fps)

        target_obj = None
        if context.active_object and context.active_object != camera:
            target_obj = context.active_object
        target_loc = get_target_location(context)

        move_type = props.move_type

        # Básicos
        if move_type == 'ORBIT':
            self.create_orbit(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('DOLLY_IN', 'DOLLY_OUT'):
            self.create_dolly(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('TRUCK_LEFT', 'TRUCK_RIGHT'):
            self.create_truck(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('PEDESTAL_UP', 'PEDESTAL_DOWN'):
            self.create_pedestal(context, camera, target_loc, start_frame, end_frame, props)

        # Cinematográficos
        elif move_type == 'CRANE':
            self.create_crane(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type == 'DOLLY_ZOOM':
            self.create_dolly_zoom(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type == 'ARC_SHOT':
            self.create_arc_shot(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type == 'WHIP_PAN':
            self.create_whip_pan(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type == 'PUSH_TILT':
            self.create_push_tilt(context, camera, target_loc, start_frame, end_frame, props)

        # Produto/Archviz
        elif move_type == 'TURNTABLE':
            self.create_turntable(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type == 'FLYTHROUGH':
            self.create_flythrough(context, camera, target_loc, start_frame, end_frame, props)
        elif move_type in ('ZOOM_IN', 'ZOOM_OUT'):
            self.create_zoom(context, camera, start_frame, end_frame, props)

        # Efeitos
        elif move_type == 'SHAKE':
            self.create_shake(context, camera, start_frame, end_frame, props)
        elif move_type == 'FOLLOW_PATH':
            self.create_follow_path(context, camera, start_frame, end_frame, props)
        elif move_type == 'RACK_FOCUS':
            self.create_rack_focus(context, camera, start_frame, end_frame, props)

        if move_type != 'SHAKE':
            set_keyframe_interpolation(camera, props.use_easing)
            set_keyframe_interpolation_camera_data(camera, props.use_easing)

        context.scene.frame_end = max(context.scene.frame_end, end_frame)

        self.report({'INFO'}, f"Movimento '{move_type}' criado: frames {start_frame}-{end_frame}")
        return {'FINISHED'}

    # --------------------------------------------------------
    # MOVIMENTOS BÁSICOS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MOVIMENTOS CINEMATOGRÁFICOS
    # --------------------------------------------------------

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

    def create_dolly_zoom(self, context, camera, target_loc, start_frame, end_frame, props):
        cam_data = camera.data

        initial_distance = (camera.location - target_loc).length
        initial_fov = cam_data.angle

        # size = distance * tan(fov/2), então: d1 * tan(fov1/2) = d2 * tan(fov2/2)
        apparent_size = initial_distance * math.tan(initial_fov / 2)

        direction = (target_loc - camera.location).normalized()
        move_dist = props.move_distance * props.dolly_zoom_intensity

        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        cam_data.keyframe_insert(data_path="angle", frame=start_frame)

        steps = 12
        for i in range(1, steps + 1):
            progress = i / steps
            frame = start_frame + int((end_frame - start_frame) * progress)

            new_pos = camera.location + direction * move_dist * progress
            new_distance = (new_pos - target_loc).length

            new_fov = 2 * math.atan(apparent_size / new_distance)
            new_fov = max(0.01, min(math.pi - 0.01, new_fov))  # Clamp

            camera.location = new_pos
            cam_data.angle = new_fov

            camera.keyframe_insert(data_path="location", frame=frame)
            cam_data.keyframe_insert(data_path="angle", frame=frame)

        context.scene.frame_set(start_frame)

    def create_arc_shot(self, context, camera, target_loc, start_frame, end_frame, props):
        offset = camera.location - target_loc
        radius = offset.length
        start_angle = math.atan2(offset.y, offset.x)
        start_height = camera.location.z

        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)

        total_angle = math.radians(props.orbit_angle)
        steps = max(8, int(abs(props.orbit_angle) / 30))

        for i in range(1, steps + 1):
            progress = i / steps
            frame = start_frame + int((end_frame - start_frame) * progress)
            angle = start_angle + (total_angle * progress)

            new_x = target_loc.x + radius * math.cos(angle)
            new_y = target_loc.y + radius * math.sin(angle)

            height_offset = props.arc_height * math.sin(progress * math.pi)
            new_z = start_height + height_offset

            camera.location.x = new_x
            camera.location.y = new_y
            camera.location.z = new_z
            camera.keyframe_insert(data_path="location", frame=frame)

        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)

    def create_whip_pan(self, context, camera, target_loc, start_frame, end_frame, props):
        """Cria rotação rápida horizontal (whip pan)"""
        initial_rotation = camera.rotation_euler.copy()

        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=start_frame)

        angle = math.radians(props.orbit_angle)
        camera.rotation_euler.z += angle
        camera.keyframe_insert(data_path="rotation_euler", frame=end_frame)

        if camera.animation_data and camera.animation_data.action:
            for fcurve in camera.animation_data.action.fcurves:
                if 'rotation' in fcurve.data_path:
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'LINEAR'

    def create_push_tilt(self, context, camera, target_loc, start_frame, end_frame, props):
        direction = (target_loc - camera.location).normalized()
        initial_rotation = camera.rotation_euler.copy()

        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=start_frame)

        camera.location += direction * props.move_distance

        camera.rotation_euler.x += math.radians(props.tilt_angle)

        camera.keyframe_insert(data_path="location", frame=end_frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=end_frame)

    # --------------------------------------------------------
    # PRODUTO / ARCHVIZ
    # --------------------------------------------------------

    def create_turntable(self, context, camera, target_loc, start_frame, end_frame, props):
        offset = camera.location - target_loc
        radius = Vector((offset.x, offset.y, 0)).length
        height = offset.z
        start_angle = math.atan2(offset.y, offset.x)

        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)

        steps = 24  # Mais steps pra movimento suave

        for i in range(1, steps + 1):
            progress = i / steps
            frame = start_frame + int((end_frame - start_frame) * progress)
            angle = start_angle + (2 * math.pi * progress)

            camera.location.x = target_loc.x + radius * math.cos(angle)
            camera.location.y = target_loc.y + radius * math.sin(angle)
            camera.location.z = target_loc.z + height

            camera.keyframe_insert(data_path="location", frame=frame)

        if props.keep_target_focus:
            add_track_constraint(camera, target_loc=target_loc)

    def create_flythrough(self, context, camera, target_loc, start_frame, end_frame, props):
        direction = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        direction.normalize()

        context.scene.frame_set(start_frame)
        camera.keyframe_insert(data_path="location", frame=start_frame)

        camera.location += direction * props.move_distance
        camera.keyframe_insert(data_path="location", frame=end_frame)

    def create_zoom(self, context, camera, start_frame, end_frame, props):
        cam_data = camera.data

        fov_start = math.radians(props.zoom_fov_start)
        fov_end = math.radians(props.zoom_fov_end)

        if props.move_type == 'ZOOM_OUT':
            fov_start, fov_end = fov_end, fov_start

        context.scene.frame_set(start_frame)
        cam_data.angle = fov_start
        cam_data.keyframe_insert(data_path="angle", frame=start_frame)

        cam_data.angle = fov_end
        cam_data.keyframe_insert(data_path="angle", frame=end_frame)

    # --------------------------------------------------------
    # EFEITOS
    # --------------------------------------------------------

    def create_shake(self, context, camera, start_frame, end_frame, props):
        """Cria efeito de câmera tremendo (handheld)"""
        initial_loc = camera.location.copy()
        initial_rot = camera.rotation_euler.copy()

        fps = context.scene.render.fps
        total_frames = end_frame - start_frame

        intensity = props.shake_intensity * 0.1
        rot_intensity = props.shake_intensity * 0.02

        frames_per_shake = max(1, int(fps / (props.shake_frequency * 4)))

        for frame in range(start_frame, end_frame + 1, frames_per_shake):
            context.scene.frame_set(frame)

            camera.location.x = initial_loc.x + random.uniform(-intensity, intensity)
            camera.location.y = initial_loc.y + random.uniform(-intensity, intensity)
            camera.location.z = initial_loc.z + random.uniform(-intensity * 0.5, intensity * 0.5)

            camera.rotation_euler.x = initial_rot.x + random.uniform(-rot_intensity, rot_intensity)
            camera.rotation_euler.y = initial_rot.y + random.uniform(-rot_intensity, rot_intensity)
            camera.rotation_euler.z = initial_rot.z + random.uniform(-rot_intensity * 0.5, rot_intensity * 0.5)

            camera.keyframe_insert(data_path="location", frame=frame)
            camera.keyframe_insert(data_path="rotation_euler", frame=frame)

        camera.location = initial_loc
        camera.rotation_euler = initial_rot
        camera.keyframe_insert(data_path="location", frame=end_frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=end_frame)

        set_keyframe_interpolation(camera, easing=False)

    def create_follow_path(self, context, camera, start_frame, end_frame, props):
        curves = [obj for obj in context.scene.objects if obj.type == 'CURVE']

        if not curves:
            bpy.ops.curve.primitive_bezier_curve_add(location=camera.location)
            curve = context.active_object
            curve.name = "QCM_CameraPath"

            spline = curve.data.splines[0]
            spline.bezier_points[0].co = Vector((0, 0, 0))
            spline.bezier_points[1].co = Vector((0, props.move_distance, 0))
        else:
            curve = curves[0]

        for c in camera.constraints:
            if c.name == "QCM_FollowPath":
                camera.constraints.remove(c)

        constraint = camera.constraints.new('FOLLOW_PATH')
        constraint.name = "QCM_FollowPath"
        constraint.target = curve
        constraint.use_curve_follow = True
        constraint.forward_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        constraint.offset = 0
        constraint.keyframe_insert(data_path="offset", frame=start_frame)

        constraint.offset = -100  # Percorre toda a curva
        constraint.keyframe_insert(data_path="offset", frame=end_frame)

    def create_rack_focus(self, context, camera, start_frame, end_frame, props):
        cam_data = camera.data

        cam_data.dof.use_dof = True

        context.scene.frame_set(start_frame)
        cam_data.dof.focus_distance = props.rack_focus_start
        cam_data.dof.keyframe_insert(data_path="focus_distance", frame=start_frame)

        cam_data.dof.focus_distance = props.rack_focus_end
        cam_data.dof.keyframe_insert(data_path="focus_distance", frame=end_frame)


# ============================================================
# OPERADORES AUXILIARES
# ============================================================

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

        if camera.data.animation_data:
            camera.data.animation_data_clear()

        if camera.data.dof.animation_data:
            camera.data.dof.animation_data_clear()

        for c in camera.constraints:
            if c.name.startswith("QCM_"):
                camera.constraints.remove(c)

        remove_qcm_objects()

        self.report({'INFO'}, "Animação da câmera removida")
        return {'FINISHED'}


class QCM_OT_preview(bpy.types.Operator):
    bl_idname = "qcm.preview"
    bl_label = "Preview"

    def execute(self, context):
        bpy.ops.screen.animation_play()
        return {'FINISHED'}


# ============================================================
# PAINEL UI
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

        layout.separator()

        move = props.move_type

        if move in ('ORBIT', 'ARC_SHOT', 'WHIP_PAN', 'TURNTABLE'):
            layout.prop(props, "orbit_angle")

        if move in ('DOLLY_IN', 'DOLLY_OUT', 'TRUCK_LEFT', 'TRUCK_RIGHT',
                    'PEDESTAL_UP', 'PEDESTAL_DOWN', 'PUSH_TILT', 'FLYTHROUGH'):
            layout.prop(props, "move_distance")

        if move == 'ARC_SHOT':
            layout.prop(props, "arc_height")

        if move == 'DOLLY_ZOOM':
            layout.prop(props, "move_distance")
            layout.prop(props, "dolly_zoom_intensity")

        if move == 'PUSH_TILT':
            layout.prop(props, "tilt_angle")

        if move in ('ZOOM_IN', 'ZOOM_OUT'):
            layout.prop(props, "zoom_fov_start")
            layout.prop(props, "zoom_fov_end")

        if move == 'SHAKE':
            layout.prop(props, "shake_intensity")
            layout.prop(props, "shake_frequency")

        if move == 'RACK_FOCUS':
            layout.prop(props, "rack_focus_start")
            layout.prop(props, "rack_focus_end")

        layout.separator()

        if move not in ('ZOOM_IN', 'ZOOM_OUT', 'SHAKE', 'RACK_FOCUS', 'WHIP_PAN'):
            layout.prop(props, "use_easing")

        if move not in ('ZOOM_IN', 'ZOOM_OUT', 'SHAKE', 'RACK_FOCUS',
                        'WHIP_PAN', 'FLYTHROUGH', 'FOLLOW_PATH', 'DOLLY_ZOOM'):
            layout.prop(props, "keep_target_focus")

        layout.separator()

        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("qcm.create_move", icon='PLAY')

        row = layout.row(align=True)
        row.operator("qcm.preview", icon='PREVIEW_RANGE')
        row.operator("qcm.clear_animation", icon='X')


# ============================================================
# REGISTRO
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