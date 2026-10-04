from config import (
    NORMAL_THRESHOLD,
    THREAT_THRESHOLD,
    ESCAPE_THRESHOLD
)


def determine_state(score):
    """
    Tehdit skoruna göre mevcut durumu belirler.

    0 - NORMAL_THRESHOLD      -> NORMAL
    NORMAL_THRESHOLD - THREAT_THRESHOLD -> THREAT
    THREAT_THRESHOLD - ESCAPE_THRESHOLD -> LOCK_RISK
    ESCAPE_THRESHOLD ve üzeri -> ESCAPE
    """

    if score < NORMAL_THRESHOLD:
        return "NORMAL"

    elif score < THREAT_THRESHOLD:
        return "THREAT"

    elif score < ESCAPE_THRESHOLD:
        return "LOCK_RISK"

    else:
        return "ESCAPE"


def state_transition(current_state, score):
    """
    Mevcut durum ve yeni skora göre
    yeni durumu hesaplar.

    Şimdilik determine_state() kullanıyor.

    İleride:
    - Histerezis
    - Zaman tabanlı geçiş
    - Durum kilitleme
    gibi mekanizmalar eklenebilir.
    """

    new_state = determine_state(score)

    if current_state == new_state:
        return current_state

    print(
        f"STATE CHANGE: "
        f"{current_state} -> {new_state}"
    )

    return new_state