import math
import numpy as np


def distance(uav, target):
    """
    3D Öklid mesafesi
    """

    return math.sqrt(
        (target.x - uav.x) ** 2 +
        (target.y - uav.y) ** 2 +
        (target.z - uav.z) ** 2
    )


def relative_position(uav, target):
    """
    Rakibin bize göre bağıl konumu
    """

    return np.array([
        target.x - uav.x,
        target.y - uav.y,
        target.z - uav.z
    ])


def relative_velocity(uav, target):
    """
    Rakibin bize göre bağıl hızı
    """

    return np.array([
        target.vx - uav.vx,
        target.vy - uav.vy,
        target.vz - uav.vz
    ])


def heading_difference(uav, target):
    """
    Rakibin bizim burun yönümüze göre açısı
    Sonuç: -180 ile +180 derece arası
    """

    rel_pos = relative_position(uav, target)

    target_heading = math.degrees(
        math.atan2(rel_pos[1], rel_pos[0])
    )

    diff = target_heading - uav.yaw

    while diff > 180:
        diff -= 360

    while diff < -180:
        diff += 360

    return diff


def calculate_ttc(uav, target):
    """
    Time To Collision (TTC)

    Yaklaşmıyorsa sonsuz döndürür.
    """

    rel_pos = relative_position(uav, target)
    rel_vel = relative_velocity(uav, target)

    dist = np.linalg.norm(rel_pos)

    if dist == 0:
        return 0

    closing_speed = -np.dot(rel_pos, rel_vel) / dist

    if closing_speed <= 0:
        return float("inf")

    return dist / closing_speed


def body_frame_transform(uav, vector):
    """
    Dünya koordinatından
    gövde koordinatına dönüşüm

    vector:
    [x,y,z]
    """

    yaw_rad = math.radians(uav.yaw)

    rotation_matrix = np.array([
        [math.cos(yaw_rad), math.sin(yaw_rad), 0],
        [-math.sin(yaw_rad), math.cos(yaw_rad), 0],
        [0, 0, 1]
    ])

    return rotation_matrix @ vector


def normalize_vector(vector):
    """
    Vektörü birim vektöre dönüştürür.
    """

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm