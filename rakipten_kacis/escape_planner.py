import math
import numpy as np

from geometry import (
    relative_velocity,
    relative_position,
    body_frame_transform,
    normalize_vector
)

from config import (
    SAFE_ESCAPE_DISTANCE,
    MIN_TURN_RADIUS
)


def calculate_escape_direction(uav, primary_target):
    """
    Rakibin bağıl hız vektörüne dik
    lateral kaçış yönü üretir.
    """

    rel_vel = relative_velocity(
        uav,
        primary_target
    )

    vx = rel_vel[0]
    vy = rel_vel[1]

    lateral = np.array([
        -vy,
         vx,
         0
    ])

    return normalize_vector(lateral)


def calculate_safe_target(
        uav,
        escape_direction):
    """
    Kaçış yönünde güvenli hedef nokta üretir.
    """

    target_x = (
        uav.x +
        escape_direction[0] *
        SAFE_ESCAPE_DISTANCE
    )

    target_y = (
        uav.y +
        escape_direction[1] *
        SAFE_ESCAPE_DISTANCE
    )

    target_z = (
        uav.z +
        escape_direction[2] *
        SAFE_ESCAPE_DISTANCE
    )

    return np.array([
        target_x,
        target_y,
        target_z
    ])


def generate_dubins_path(
        uav,
        safe_target):
    """
    İlk sürüm.

    Gerçek Dubins yerine
    uygulanabilir waypointler üretir.
    """

    start = np.array([
        uav.x,
        uav.y,
        uav.z
    ])

    end = safe_target

    direction = end - start

    distance = np.linalg.norm(
        direction
    )

    if distance == 0:
        return [start]

    direction = direction / distance

    waypoint_count = 5

    path = []

    for i in range(
            waypoint_count + 1):

        ratio = (
            i /
            waypoint_count
        )

        point = (
            start +
            direction *
            distance *
            ratio
        )

        path.append(point)

    return path


def validate_path(path):
    """
    Yolun uygulanabilirliğini kontrol eder.

    İlk sürümde:

    - Yol boş mu?
    - Waypoint sayısı yeterli mi?

    kontrol edilir.
    """

    if path is None:
        return False

    if len(path) < 2:
        return False

    return True