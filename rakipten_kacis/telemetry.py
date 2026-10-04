class UAV:

    def __init__(
        self,
        x,
        y,
        z,
        vx,
        vy,
        vz,
        yaw
    ):

        self.x = x
        self.y = y
        self.z = z

        self.vx = vx
        self.vy = vy
        self.vz = vz

        self.yaw = yaw


class Target:

    def __init__(
        self,
        target_id,
        x,
        y,
        z,
        vx,
        vy,
        vz
    ):

        self.id = target_id

        self.x = x
        self.y = y
        self.z = z

        self.vx = vx
        self.vy = vy
        self.vz = vz

        self.threat_time = 0.0


def get_telemetry():

    uav = UAV(
        x=0,
        y=0,
        z=100,

        vx=20,
        vy=0,
        vz=0,

        yaw=0
    )

    targets = [

        Target(
            target_id=1,

            x=80,
            y=20,
            z=100,

            vx=-10,
            vy=0,
            vz=0
        ),

        Target(
            target_id=2,

            x=150,
            y=120,
            z=100,

            vx=-5,
            vy=-2,
            vz=0
        ),

        Target(
            target_id=3,

            x=250,
            y=50,
            z=100,

            vx=-3,
            vy=0,
            vz=0
        )
    ]

    return uav, targets