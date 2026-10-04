import math

from geometry import (
    distance,
    relative_velocity,
    heading_difference,
    calculate_ttc
)

from config import (
    THREAT_RADIUS,
    W_DISTANCE,
    W_SPEED,
    W_HEADING,
    W_TTC,
    W_TIME
)


def apply_kalman_filter(target):
    """
    İlk sürüm:
    Filtre uygulanmıyor.
    Daha sonra gerçek Kalman eklenecek.
    """

    return target


def is_inside_threat_radius(uav, target):
    """
    Rakip tehdit yarıçapı içinde mi?
    """

    dist = distance(uav, target)

    return dist <= THREAT_RADIUS


def is_inside_heading_sector(uav, target):
    """
    ±90 derece ön yarımküre kontrolü
    """

    angle = heading_difference(uav, target)

    return abs(angle) <= 90


def update_threat_time(target, dt=1.0):
    """
    Tehdit alanında kalma süresini günceller
    """

    target.threat_time += dt

    return target.threat_time


def compute_distance_factor(dist):
    """
    Yaklaştıkça skor artsın
    Sonuç 0-1
    """

    factor = 1.0 - (dist / THREAT_RADIUS)

    return max(0.0, min(1.0, factor))


def compute_speed_factor(rel_speed):
    """
    Bağıl hız arttıkça tehdit artsın
    """

    MAX_REL_SPEED = 50.0

    factor = rel_speed / MAX_REL_SPEED

    return max(0.0, min(1.0, factor))


def compute_heading_factor(angle):
    """
    Burun doğrultusuna yaklaştıkça skor artsın

    0 derece -> 1.0
    90 derece -> 0.0
    """

    factor = 1.0 - (abs(angle) / 90.0)

    return max(0.0, min(1.0, factor))


def compute_ttc_factor(ttc):
    """
    TTC küçüldükçe tehdit artsın
    """

    if math.isinf(ttc):
        return 0.0

    MAX_TTC = 30.0

    factor = 1.0 - (ttc / MAX_TTC)

    return max(0.0, min(1.0, factor))


def compute_time_factor(threat_time):
    """
    Tehdit alanında uzun süre kalan
    daha riskli kabul edilir
    """

    MAX_TIME = 20.0

    factor = threat_time / MAX_TIME

    return max(0.0, min(1.0, factor))


def compute_threat_score(
        distance_factor,
        speed_factor,
        heading_factor,
        ttc_factor,
        time_factor):
    """
    Toplam tehdit skoru
    """

    score = (
        W_DISTANCE * distance_factor +
        W_SPEED * speed_factor +
        W_HEADING * heading_factor +
        W_TTC * ttc_factor +
        W_TIME * time_factor
    )

    return score * 100.0


def detect_primary_threat(uav, targets):
    """
    En yüksek tehdit skoruna sahip
    rakibi bulur
    """

    best_score = 0.0

    primary_target = None

    for target in targets:

        target = apply_kalman_filter(target)

        if not is_inside_threat_radius(uav, target):
            continue

        update_threat_time(target)

        dist = distance(uav, target)

        rel_vel = relative_velocity(uav, target)

        rel_speed = math.sqrt(
            rel_vel[0] ** 2 +
            rel_vel[1] ** 2 +
            rel_vel[2] ** 2
        )

        angle = heading_difference(uav, target)

        ttc = calculate_ttc(uav, target)

        distance_factor = compute_distance_factor(dist)

        speed_factor = compute_speed_factor(rel_speed)

        heading_factor = compute_heading_factor(angle)

        ttc_factor = compute_ttc_factor(ttc)

        time_factor = compute_time_factor(
            target.threat_time
        )

        score = compute_threat_score(
            distance_factor,
            speed_factor,
            heading_factor,
            ttc_factor,
            time_factor
        )

        if score > best_score:

            best_score = score

            primary_target = target

    return primary_target, best_score