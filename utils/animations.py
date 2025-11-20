"""
Animation generator using Manim
Generates animated backgrounds for videos
"""
import os
import asyncio
from typing import Optional

# Try to import manim - make it optional
try:
    from manim import *
    import numpy as np
    import random
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False
    print("Warning: Manim not available. Animation features will be disabled.")


class BaseAnimation:
    """Base class for all animations"""

    def __init__(self, duration: int = 10):
        self.duration = duration
        self.colors = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, PINK, TEAL]

    def get_random_color(self):
        """Get random color"""
        return random.choice(self.colors)

    def get_gradient_colors(self, count: int = 2):
        """Get gradient colors"""
        return random.sample(self.colors, min(count, len(self.colors)))


class OrbitEscapeBall(BaseAnimation):
    """Ball orbiting rings with periodic escapes"""

    def construct(self, scene: Scene):
        # Black background with stars
        scene.camera.background_color = "#000000"

        # Stars background
        stars = VGroup()
        for _ in range(20):
            star = Dot(
                point=[random.uniform(-7, 7), random.uniform(-4, 4), 0],
                radius=0.015,
                color=WHITE,
                fill_opacity=random.uniform(0.3, 0.8)
            )
            stars.add(star)
        scene.add(stars)

        # Rings
        num_rings = 4
        ring_radii = [0.8, 1.6, 2.4, 3.2]
        rings = VGroup()

        for i, radius in enumerate(ring_radii):
            ring = Circle(radius=radius, color=WHITE, stroke_width=2, stroke_opacity=0.7)
            rings.add(ring)

        scene.add(rings)

        # Ball
        ball = Dot(radius=0.12, color=YELLOW, fill_opacity=1)
        ball.move_to([ring_radii[0], 0, 0])

        # Trail
        trail = TracedPath(
            ball.get_center,
            stroke_color=[YELLOW, ORANGE, RED],
            stroke_width=3,
            dissipating_time=0.5,
            stroke_opacity=[0.7, 0.5, 0.3]
        )
        scene.add(trail, ball)

        # Animation parameters - loop continuously until duration is reached
        orbit_time = 3.0
        escape_time = 1.5
        total_time = 0.0

        # Loop animation continuously
        while total_time < self.duration:
            # Choose random ring to orbit
            ring_idx = random.randint(0, num_rings - 1)
            orbit_radius = ring_radii[ring_idx]

            # Orbit around ring
            scene.play(
                Rotate(ball, angle=TAU, about_point=ORIGIN),
                Rotate(rings[ring_idx], angle=-TAU/3),
                run_time=orbit_time,
                rate_func=linear
            )
            total_time += orbit_time

            if total_time >= self.duration:
                break

            # Escape from ring
            escape_angle = random.uniform(0, TAU)
            escape_distance = random.uniform(4, 5.5)
            escape_point = np.array([
                np.cos(escape_angle) * escape_distance,
                np.sin(escape_angle) * escape_distance,
                0
            ])

            scene.play(
                ball.animate.move_to(escape_point).scale(1.3),
                run_time=escape_time * 0.5,
                rate_func=rush_from
            )
            total_time += escape_time * 0.5

            if total_time >= self.duration:
                break

            # Return to ring
            return_point = np.array([
                np.cos(escape_angle + PI) * orbit_radius,
                np.sin(escape_angle + PI) * orbit_radius,
                0
            ])

            scene.play(
                ball.animate.move_to(return_point).scale(1/1.3),
                run_time=escape_time * 0.5,
                rate_func=rush_into
            )
            total_time += escape_time * 0.5


class MultiOrbitBalls(BaseAnimation):
    """Multiple balls orbiting between rings"""

    def construct(self, scene: Scene):
        # Black background
        scene.camera.background_color = "#000000"

        # Animated background gradient
        background = Rectangle(
            width=14, height=8,
            fill_color=[DARK_BLUE, BLACK],
            fill_opacity=1,
            stroke_width=0
        )
        scene.add(background)

        # Concentric rings
        num_rings = 5
        ring_radii = [0.6, 1.2, 1.8, 2.4, 3.0]
        rings = VGroup()

        for radius in ring_radii:
            ring = Circle(
                radius=radius,
                color=BLUE,
                stroke_width=2,
                stroke_opacity=0.5
            )
            rings.add(ring)

        scene.add(rings)

        # Create multiple balls
        num_balls = 6
        balls = VGroup()
        ball_colors = [RED, YELLOW, GREEN, BLUE, PURPLE, ORANGE]

        for i in range(num_balls):
            angle = i * TAU / num_balls
            ring_idx = i % len(ring_radii)
            radius = ring_radii[ring_idx]

            ball = Dot(
                radius=0.10,
                color=ball_colors[i],
                fill_opacity=1
            )
            ball.move_to([
                np.cos(angle) * radius,
                np.sin(angle) * radius,
                0
            ])
            balls.add(ball)

        # Trails
        trails = VGroup()
        for ball in balls:
            trail = TracedPath(
                ball.get_center,
                stroke_color=ball.get_color(),
                stroke_width=2,
                dissipating_time=0.4,
                stroke_opacity=[0.6, 0.4, 0.2]
            )
            trails.add(trail)
            scene.add(trail)

        scene.add(balls)

        # Rotate rings in different directions
        ring_rotations = [
            Rotate(rings[i], angle=(-1 if i % 2 == 0 else 1) * TAU / 8, rate_func=linear)
            for i in range(num_rings)
        ]

        # Animation loop
        segment_time = 2.0
        num_segments = int(self.duration / segment_time)

        for _ in range(num_segments):
            # Create orbital rotations for all balls
            ball_anims = []
            for i, ball in enumerate(balls):
                ring_idx = i % len(ring_radii)
                rotation_speed = (1 if i % 2 == 0 else -1) * TAU / (2 + i * 0.2)
                ball_anims.append(
                    Rotate(ball, angle=rotation_speed, about_point=ORIGIN, rate_func=linear)
                )

            scene.play(
                *ball_anims,
                *ring_rotations,
                run_time=segment_time,
                rate_func=linear
            )


class PulsatingRings(BaseAnimation):
    """Pulsating rings with central ball"""

    def construct(self, scene: Scene):
        # Dark background with gradient
        scene.camera.background_color = "#0a0a0a"

        # Central glowing ball
        ball = Dot(radius=0.20, color=YELLOW, fill_opacity=1)
        ball_glow = Circle(
            radius=0.30,
            color=YELLOW,
            fill_opacity=0.3,
            stroke_width=0
        )
        scene.add(ball_glow, ball)

        # Pulsating rings
        num_rings = 6
        rings = VGroup()
        base_colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]

        for i in range(num_rings):
            ring = Circle(
                radius=(i + 1) * 0.5,
                color=base_colors[i],
                stroke_width=3,
                stroke_opacity=0.7
            )
            rings.add(ring)

        scene.add(rings)

        # Orbiting particles
        particles = VGroup()
        num_particles = 12
        for i in range(num_particles):
            angle = i * TAU / num_particles
            distance = 2.5
            particle = Dot(
                radius=0.05,
                color=WHITE,
                fill_opacity=0.8
            )
            particle.move_to([
                np.cos(angle) * distance,
                np.sin(angle) * distance,
                0
            ])
            particles.add(particle)

        scene.add(particles)

        # Animation loop
        pulse_time = 1.5
        num_pulses = int(self.duration / pulse_time)

        for pulse in range(num_pulses):
            # Pulsate rings
            ring_anims = []
            for i, ring in enumerate(rings):
                scale_factor = 1.2 if pulse % 2 == 0 else 0.8
                ring_anims.append(ring.animate.scale(scale_factor))

            # Rotate particles
            particle_rotation = Rotate(
                particles,
                angle=TAU / num_particles,
                about_point=ORIGIN,
                rate_func=linear
            )

            # Pulsate central ball glow
            glow_anim = ball_glow.animate.scale(1.3 if pulse % 2 == 0 else 0.77)

            scene.play(
                *ring_anims,
                particle_rotation,
                glow_anim,
                run_time=pulse_time,
                rate_func=smooth
            )


class FreezingBalls(BaseAnimation):
    """Balls fall into ring, freeze, one escapes with confetti"""

    def __init__(self, duration: int = 10):
        super().__init__(duration)
        self.cycle_count = 0

    def construct(self, scene: Scene):
        # Black background with stars
        scene.camera.background_color = "#000000"

        # Stars background (persistent across cycles)
        stars = VGroup()
        star_velocities = []
        for _ in range(15):
            star = Dot(
                point=[random.uniform(-7, 7), random.uniform(-4, 4), 0],
                radius=0.02,
                color=WHITE
            )
            stars.add(star)
            star_velocities.append([
                random.uniform(-0.3, 0.3),
                random.uniform(-0.3, 0.3)
            ])

        def update_stars(mob, dt):
            for i, star in enumerate(mob):
                new_pos = star.get_center()
                new_pos[0] += star_velocities[i][0] * dt
                new_pos[1] += star_velocities[i][1] * dt

                if new_pos[0] < -7:
                    new_pos[0] = 7
                elif new_pos[0] > 7:
                    new_pos[0] = -7
                if new_pos[1] < -4:
                    new_pos[1] = 4
                elif new_pos[1] > 4:
                    new_pos[1] = -4

                star.move_to(new_pos)

        stars.add_updater(update_stars)
        scene.add(stars)

        # Track total elapsed time for looping
        total_elapsed = 0.0

        # Loop the animation until duration is reached
        while total_elapsed < self.duration:
            cycle_duration = self._run_single_cycle(scene)
            total_elapsed += cycle_duration

    def _run_single_cycle(self, scene: Scene) -> float:
        """Run a single cycle of the freezing balls animation. Returns cycle duration."""

        # Ring with gap at top
        ring_radius = 3.0
        gap_size = 0.8
        gap_angle = PI / 2  # Top

        freeze_ring = Arc(
            radius=ring_radius,
            start_angle=gap_angle + gap_size / 2,
            angle=TAU - gap_size,
            stroke_width=6
        ).move_to(ORIGIN)
        freeze_ring.set_stroke(BLUE, width=6, opacity=0.9)
        scene.add(freeze_ring)

        # Parameters
        BALL_RADIUS = 0.15
        GRAVITY = 9.8
        FREEZE_TIME = 2.0
        fps = 60
        dt = 1.0 / fps

        # Physics simulation
        class Ball:
            def __init__(self, spawn_time):
                self.pos = np.array([0.0, ring_radius + 0.5, 0.0])
                self.vel = np.array([random.uniform(-1.0, 1.0), 0.0, 0.0])
                self.color = random.choice([YELLOW, ORANGE, RED, GREEN, PURPLE, PINK])
                self.spawn_time = spawn_time
                self.freeze_time = spawn_time + FREEZE_TIME
                self.frozen = False
                self.positions = []
                self.exited = False
                self.entered_ring = False
                self.bounced = False

        balls = []
        current_time = 0
        simulation_done = False
        max_simulation_time = 30
        can_spawn_new = True

        frame = 0
        while not simulation_done and current_time < max_simulation_time:
            if can_spawn_new:
                balls.append(Ball(current_time))
                can_spawn_new = False

            for ball in balls:
                if ball.exited:
                    continue

                if not ball.frozen and current_time >= ball.freeze_time:
                    ball.frozen = True
                    ball.vel = np.array([0.0, 0.0, 0.0])
                    if ball is balls[-1]:
                        can_spawn_new = True

                if not ball.frozen:
                    ball.vel[1] -= GRAVITY * dt
                    new_pos = ball.pos + ball.vel * dt

                    dist = np.sqrt(new_pos[0]**2 + new_pos[1]**2)

                    if dist > 0.1:
                        angle = np.arctan2(new_pos[1], new_pos[0]) % TAU
                        angle_diff = min(abs(angle - gap_angle), TAU - abs(angle - gap_angle))
                        in_gap = angle_diff < gap_size / 2

                        if dist < ring_radius - BALL_RADIUS:
                            ball.entered_ring = True

                        if in_gap and ball.entered_ring and dist > ring_radius + BALL_RADIUS:
                            ball.exited = True
                            simulation_done = True

                        if not in_gap and not ball.exited and abs(dist - ring_radius) < BALL_RADIUS + 0.15:
                            normal = np.array([new_pos[0] / dist, new_pos[1] / dist, 0.0])
                            vel_along_normal = np.dot(ball.vel, normal)

                            should_bounce = False
                            if dist < ring_radius:
                                should_bounce = vel_along_normal > 0
                            else:
                                should_bounce = vel_along_normal < 0

                            if should_bounce:
                                ball.vel = ball.vel - 2 * vel_along_normal * normal
                                ball.vel *= 0.8

                                if ball.entered_ring:
                                    ball.bounced = True

                                if dist < ring_radius:
                                    new_pos[:2] = normal[:2] * (ring_radius - BALL_RADIUS - 0.1)
                                else:
                                    new_pos[:2] = normal[:2] * (ring_radius + BALL_RADIUS + 0.1)

                    # Collisions with other balls
                    for other in balls:
                        if other is ball or other.exited:
                            continue

                        diff = new_pos - other.pos
                        distance = np.linalg.norm(diff[:2])

                        if distance < 2 * BALL_RADIUS and distance > 0.01:
                            normal = diff / distance
                            vel_towards_other = np.dot(ball.vel, -normal)

                            if vel_towards_other > 0:
                                if other.frozen:
                                    vel_along_normal = np.dot(ball.vel, normal)
                                    ball.vel = ball.vel - 2 * vel_along_normal * normal
                                    ball.vel *= 0.9

                                    if ball.entered_ring:
                                        ball.bounced = True

                                    overlap = 2 * BALL_RADIUS - distance
                                    new_pos[:2] += normal[:2] * (overlap + 0.1)
                                else:
                                    relative_vel = ball.vel - other.vel
                                    vel_along_normal = np.dot(relative_vel, normal)

                                    if vel_along_normal < 0:
                                        impulse = normal * vel_along_normal
                                        ball.vel -= impulse
                                        other.vel += impulse

                                        if ball.entered_ring:
                                            ball.bounced = True
                                        if other.entered_ring:
                                            other.bounced = True

                                        overlap = 2 * BALL_RADIUS - distance
                                        separation = normal * (overlap / 2 + 0.05)
                                        new_pos[:2] += separation[:2]
                                        other.pos[:2] -= separation[:2]

                    ball.pos = new_pos.copy()

                ball.positions.append(ball.pos.copy())

            current_time += dt
            frame += 1

        # Rendering
        all_balls_group = VGroup()
        ball_objects = []
        ball_trails = []

        for ball_data in balls:
            if not ball_data.positions:
                continue

            ball_obj = Dot(radius=BALL_RADIUS, color=ball_data.color)
            ball_obj.set_fill(ball_data.color, opacity=1)
            ball_obj.move_to(ball_data.positions[0])
            ball_obj.ball_data = ball_data

            trail = TracedPath(
                ball_obj.get_center,
                stroke_color=[RED, ORANGE, YELLOW],
                stroke_width=3,
                dissipating_time=0.5
            )

            ball_objects.append(ball_obj)
            ball_trails.append(trail)
            all_balls_group.add(ball_obj)

        for trail in ball_trails:
            scene.add(trail)
        scene.add(all_balls_group)

        # Updater
        animation_time = [0]
        last_freeze_check = [set()]
        confetti_triggered = [False]
        confetti_group = VGroup()

        def update_all_balls(mob, dt):
            animation_time[0] += dt
            current_frame = int(animation_time[0] * fps)

            for ball_obj in ball_objects:
                ball_data = ball_obj.ball_data
                spawn_frame = int(ball_data.spawn_time * fps)
                local_frame = current_frame - spawn_frame

                if animation_time[0] < ball_data.spawn_time:
                    ball_obj.set_opacity(0)
                else:
                    ball_obj.set_opacity(1)

                if 0 <= local_frame < len(ball_data.positions):
                    ball_obj.move_to(ball_data.positions[local_frame])

                    if (ball_data.frozen and
                        id(ball_obj) not in last_freeze_check[0] and
                        animation_time[0] >= ball_data.freeze_time):
                        last_freeze_check[0].add(id(ball_obj))
                        ball_obj.set_color(BLUE_B)

                    if not confetti_triggered[0] and ball_data.exited and ball_data.bounced:
                        pos = ball_obj.get_center()
                        dist = np.sqrt(pos[0]**2 + pos[1]**2)

                        if dist > 0.1:
                            angle = np.arctan2(pos[1], pos[0]) % TAU
                            angle_diff = min(abs(angle - gap_angle), TAU - abs(angle - gap_angle))
                            in_gap = angle_diff < gap_size / 2

                            if in_gap and dist > ring_radius + BALL_RADIUS * 2:
                                confetti_triggered[0] = True
                                create_confetti(scene, confetti_group, [pos[0], pos[1], 0])

        all_balls_group.add_updater(update_all_balls)

        def create_confetti(scene, group, origin_point):
            particles = []
            colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, WHITE]

            for _ in range(200):
                width = random.uniform(0.06, 0.12)
                height = random.uniform(0.12, 0.20)
                particle = Rectangle(
                    width=width,
                    height=height,
                    fill_color=random.choice(colors),
                    fill_opacity=1.0,
                    stroke_width=0
                )

                particle.move_to(origin_point)
                particle.rotate(random.uniform(0, TAU))

                angle = random.uniform(0, TAU)
                speed = random.uniform(3.0, 7.0)

                particle.velocity_x = speed * np.cos(angle)
                particle.velocity_y = speed * np.sin(angle)

                if random.random() < 0.6:
                    particle.velocity_y = abs(particle.velocity_y) * random.uniform(1.0, 1.5)

                particle.rotation_speed = random.uniform(-15, 15)
                particles.append(particle)
                group.add(particle)

            scene.add(group)

            confetti_time = [0]

            def update_confetti(mob, dt):
                confetti_time[0] += dt

                for particle in particles:
                    particle.velocity_y -= 15.0 * dt
                    particle.velocity_x *= 0.97
                    particle.velocity_y *= 0.97

                    new_pos = particle.get_center()
                    new_pos[0] += particle.velocity_x * dt
                    new_pos[1] += particle.velocity_y * dt
                    particle.move_to(new_pos)

                    particle.rotate(particle.rotation_speed * dt)
                    particle.rotation_speed *= 0.98

                    if confetti_time[0] > 0.5:
                        fade_factor = max(0, 1 - (confetti_time[0] - 0.5) / 2.0)
                        particle.set_opacity(fade_factor)

                if confetti_time[0] > 2.5:
                    scene.remove(group)
                    group.remove_updater(update_confetti)

            group.add_updater(update_confetti)

        # Wait for the cycle to complete (simulation + confetti time)
        cycle_wait_time = current_time + 4.5
        scene.wait(cycle_wait_time)

        # Clean up for next cycle
        all_balls_group.remove_updater(update_all_balls)
        scene.remove(freeze_ring)
        scene.remove(all_balls_group)
        for trail in ball_trails:
            scene.remove(trail)
        if confetti_group in scene.mobjects:
            scene.remove(confetti_group)

        # Return the actual duration of this cycle
        return cycle_wait_time


class BouncingBallRings(BaseAnimation):
    """Bouncing ball with realistic physics"""

    def construct(self, scene: Scene):
        # Black background with stars
        scene.camera.background_color = "#000000"

        # Stars with movement
        stars = VGroup()
        star_velocities = []
        for _ in range(15):
            star = Dot(
                point=[random.uniform(-7, 7), random.uniform(-4, 4), 0],
                radius=0.02,
                color=WHITE
            )
            stars.add(star)
            star_velocities.append([
                random.uniform(-0.3, 0.3),
                random.uniform(-0.3, 0.3)
            ])

        def update_stars(mob, dt):
            for i, star in enumerate(mob):
                new_pos = star.get_center()
                new_pos[0] += star_velocities[i][0] * dt
                new_pos[1] += star_velocities[i][1] * dt

                if new_pos[0] < -7:
                    new_pos[0] = 7
                elif new_pos[0] > 7:
                    new_pos[0] = -7
                if new_pos[1] < -4:
                    new_pos[1] = 4
                elif new_pos[1] > 4:
                    new_pos[1] = -4

                star.move_to(new_pos)

        stars.add_updater(update_stars)
        scene.add(stars)

        # Physics parameters
        fps = 60
        total_frames = int(self.duration * fps)
        dt = 1.0 / fps

        GRAVITY = 18.0
        BOUNCE = 1.01
        BALL_RADIUS = 0.15
        MIN_VELOCITY = 2.0

        # Rings
        num_rings = 3
        ring_radii = [1.5, 2.3, 3.1]
        gap_angles = [random.uniform(0, TAU) for _ in range(num_rings)]
        gap_size = 0.45

        rotation_speeds = [random.choice([-0.6, 0.6]) for _ in range(num_rings)]

        # Pre-calculate physics
        pos = np.array([0.0, 0.0, 0.0])
        vel = np.array([random.uniform(-4, 4), 6.0, 0.0])

        ball_positions = []
        destroyed_rings = []
        active_rings = set(range(num_rings))

        for frame in range(total_frames):
            vel[1] -= GRAVITY * dt
            new_pos = pos + vel * dt

            dist = np.sqrt(new_pos[0]**2 + new_pos[1]**2)

            if dist > 0.1:
                angle = np.arctan2(new_pos[1], new_pos[0]) % TAU

                for ring_idx in list(active_rings):
                    ring_r = ring_radii[ring_idx]

                    if abs(dist - ring_r) < BALL_RADIUS + 0.1:
                        current_gap = (gap_angles[ring_idx] + rotation_speeds[ring_idx] * frame * dt) % TAU
                        angle_diff = min(abs(angle - current_gap), TAU - abs(angle - current_gap))

                        if angle_diff < gap_size / 2:
                            destroyed_rings.append((frame, ring_idx))
                            active_rings.remove(ring_idx)
                            break
                        else:
                            normal = np.array([new_pos[0] / dist, new_pos[1] / dist, 0.0])
                            vel_along_normal = np.dot(vel, normal)
                            vel = vel - 2 * vel_along_normal * normal
                            vel *= BOUNCE

                            vel_normal = np.dot(vel, normal)
                            MIN_BOUNCE_SPEED = 3.5
                            if abs(vel_normal) < MIN_BOUNCE_SPEED:
                                if dist < ring_r:
                                    vel -= normal * MIN_BOUNCE_SPEED
                                else:
                                    vel += normal * MIN_BOUNCE_SPEED

                            if dist < ring_r:
                                new_pos[:2] = normal[:2] * (ring_r - BALL_RADIUS - 0.1)
                            else:
                                new_pos[:2] = normal[:2] * (ring_r + BALL_RADIUS + 0.1)
                            break

            # Screen boundaries
            if new_pos[1] < -3.5:
                new_pos[1] = -3.5
                vel[1] = abs(vel[1]) * BOUNCE
            elif new_pos[1] > 3.5:
                new_pos[1] = 3.5
                vel[1] = -abs(vel[1]) * BOUNCE

            if new_pos[0] < -6.5:
                new_pos[0] = -6.5
                vel[0] = abs(vel[0]) * BOUNCE
            elif new_pos[0] > 6.5:
                new_pos[0] = 6.5
                vel[0] = -abs(vel[0]) * BOUNCE

            speed = np.sqrt(vel[0]**2 + vel[1]**2)
            if speed < MIN_VELOCITY and speed > 0.1:
                scale = MIN_VELOCITY / speed
                vel *= scale

            pos = new_pos.copy()
            ball_positions.append(pos.copy())

        # Rendering
        rings = VGroup()
        rings_active = [True] * num_rings

        for i in range(num_rings):
            ring = self.create_ring_with_gap(ring_radii[i], gap_angles[i], gap_size)
            ring.set_stroke(WHITE, width=3, opacity=0.9)
            rings.add(ring)

        scene.add(rings)

        # Ball
        ball = Dot(radius=BALL_RADIUS, color=YELLOW)
        ball.set_fill(YELLOW, opacity=1)
        ball.move_to(ball_positions[0])

        # Trail
        trail = TracedPath(
            ball.get_center,
            stroke_color=[RED, ORANGE, YELLOW],
            stroke_width=4,
            dissipating_time=0.3,
            stroke_opacity=[0.8, 0.6, 0.4]
        )
        scene.add(trail, ball)

        # Animation
        destroyed_rings.sort()

        segment_time = 0.2
        num_segments = int(self.duration / segment_time)
        frames_per_segment = int(total_frames / num_segments)

        current_frame = 0
        destroyed_dict = {frame: ring_idx for frame, ring_idx in destroyed_rings}

        for segment in range(num_segments):
            start_frame = current_frame
            end_frame = min(current_frame + frames_per_segment, total_frames)

            if end_frame <= start_frame:
                break

            segment_positions = ball_positions[start_frame:end_frame]

            if len(segment_positions) < 2:
                break

            path = VMobject()
            path.set_points_as_corners(segment_positions)

            anims = [MoveAlongPath(ball, path, rate_func=linear)]

            for ring_idx, ring in enumerate(rings):
                if rings_active[ring_idx]:
                    rotation = rotation_speeds[ring_idx] * segment_time
                    anims.append(Rotate(ring, angle=rotation, rate_func=linear))

            scene.play(*anims, run_time=segment_time, rate_func=linear)

            for frame in range(start_frame, end_frame):
                if frame in destroyed_dict:
                    ring_idx = destroyed_dict[frame]
                    if rings_active[ring_idx]:
                        ring = rings[ring_idx]
                        ring_center = ring.get_center()

                        particles = VGroup()
                        for i in range(12):
                            angle = i * TAU / 12
                            particle = Dot(radius=0.08, color=WHITE).move_to(ring_center)
                            particles.add(particle)

                        scene.add(particles)

                        particle_anims = []
                        for i, particle in enumerate(particles):
                            angle = i * TAU / 12
                            direction = np.array([np.cos(angle), np.sin(angle), 0])
                            target = ring_center + direction * 2.5
                            particle_anims.extend([
                                particle.animate.move_to(target),
                                particle.animate.set_opacity(0)
                            ])

                        scene.play(
                            ring.animate.scale(1.3).set_stroke(opacity=0),
                            *particle_anims,
                            run_time=0.3,
                            rate_func=rush_from
                        )

                        scene.remove(particles)
                        rings_active[ring_idx] = False

            current_frame = end_frame

    def create_ring_with_gap(self, radius: float, gap_angle: float, gap_size: float = 0.6):
        arc = Arc(
            radius=radius,
            start_angle=gap_angle + gap_size/2,
            angle=TAU - gap_size,
            stroke_width=4
        )
        return arc


class BouncingBallRingsScene(Scene):
    def construct(self):
        animation = BouncingBallRings(duration=10)
        animation.construct(self)


class AnimationGenerator:
    """Main animation generator"""

    def __init__(self, output_dir: str = "./out/animations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        if not MANIM_AVAILABLE:
            raise ImportError(
                "Manim is not installed. Animation features are not available.\n"
                "To use animations, install manim separately: pip install manim"
            )

    async def generate_animation(
        self,
        animation_type: str,
        duration: int,
        output_path: Optional[str] = None,
        resolution: str = "1080p"
    ) -> str:
        """
        Generate animation video

        Args:
            animation_type: Type of animation ('bouncing_ball_rings', etc.)
            duration: Duration in seconds
            output_path: Output path (auto-generated if None)
            resolution: Video resolution

        Returns:
            Path to generated video
        """
        if output_path is None:
            output_path = os.path.join(
                self.output_dir,
                f"{animation_type}_{duration}s.mp4"
            )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create temporary scene class
        class TempScene(Scene):
            def construct(self):
                if animation_type == "bouncing_ball_rings":
                    anim = BouncingBallRings(duration=duration)
                    anim.construct(self)
                elif animation_type == "freezing_balls":
                    anim = FreezingBalls(duration=duration)
                    anim.construct(self)
                elif animation_type == "orbit_escape_ball":
                    anim = OrbitEscapeBall(duration=duration)
                    anim.construct(self)
                elif animation_type == "multi_orbit_balls":
                    anim = MultiOrbitBalls(duration=duration)
                    anim.construct(self)
                elif animation_type == "pulsating_rings":
                    anim = PulsatingRings(duration=duration)
                    anim.construct(self)

        # Configure manim
        # Map resolution to manim quality presets
        quality_map = {
            "4k": "fourk_quality",
            "1440p": "production_quality",
            "1080p": "high_quality",
            "720p": "medium_quality",
            "480p": "low_quality"
        }
        config.quality = quality_map.get(resolution, "high_quality")
        config.output_file = os.path.basename(output_path)
        config.media_dir = os.path.dirname(output_path)
        config.disable_caching = True
        config.write_to_movie = True
        config.pixel_height = 1920
        config.pixel_width = 1080
        config.frame_rate = 60

        # Render scene
        def render_scene():
            scene = TempScene()
            scene.render()
            return scene.renderer.file_writer.movie_file_path

        # Render in thread and get actual output path
        actual_output = await asyncio.to_thread(render_scene)

        # Move file to desired location if different
        if actual_output and os.path.exists(actual_output):
            if os.path.abspath(actual_output) != os.path.abspath(output_path):
                import shutil
                shutil.move(actual_output, output_path)
            return output_path

        return output_path

    def get_available_animations(self) -> list:
        """Get list of available animation types"""
        return [
            {
                "type": "bouncing_ball_rings",
                "name": "Прыгающий шарик с кольцами",
                "description": "Шарик прыгает внутри вращающихся колец с физикой"
            },
            {
                "type": "freezing_balls",
                "name": "Замерзающие шарики с конфетти",
                "description": "Шары падают в кольцо, застывают, один вылетает с фейерверком"
            },
            {
                "type": "orbit_escape_ball",
                "name": "Шарик с орбитами и вырывами",
                "description": "Шарик орбитирует вокруг колец и периодически вырывается"
            },
            {
                "type": "multi_orbit_balls",
                "name": "Множество орбитирующих шариков",
                "description": "Несколько разноцветных шариков орбитируют между кольцами"
            },
            {
                "type": "pulsating_rings",
                "name": "Пульсирующие кольца",
                "description": "Центральный шарик окружен пульсирующими цветными кольцами"
            }
        ]
