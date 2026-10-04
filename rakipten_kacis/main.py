from telemetry import get_telemetry

from threat_detector import (
    detect_primary_threat
)

from state_machine import (
    determine_state
)

from escape_planner import (
    calculate_escape_direction,
    calculate_safe_target,
    generate_dubins_path,
    validate_path
)


def main():

    print("\nSistem Baslatildi\n")

    current_state = "NORMAL"

    uav, targets = get_telemetry()

    primary_target, score = (
        detect_primary_threat(
            uav,
            targets
        )
    )

    print(
        f"Tehdit Skoru: {score:.2f}"
    )

    current_state = determine_state(
        score
    )

    print(
        f"Durum: {current_state}"
    )

    if primary_target is not None:

        print(
            f"Birincil Tehdit: "
            f"{primary_target.id}"
        )

    else:

        print(
            "Birincil tehdit bulunamadi."
        )

    if (
        current_state == "ESCAPE"
        and
        primary_target is not None
    ):

        print(
            "\nKACIS MODU AKTIF\n"
        )

        escape_direction = (
            calculate_escape_direction(
                uav,
                primary_target
            )
        )

        safe_target = (
            calculate_safe_target(
                uav,
                escape_direction
            )
        )

        path = (
            generate_dubins_path(
                uav,
                safe_target
            )
        )

        if validate_path(path):

            print(
                "Kacis rotasi olusturuldu."
            )

            print(
                "\nWaypointler:"
            )

            for i, wp in enumerate(path):

                print(
                    f"WP{i}: {wp}"
                )

        else:

            print(
                "Gecersiz rota."
            )


if __name__ == "__main__":
    main()