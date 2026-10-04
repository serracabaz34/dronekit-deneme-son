'''
# kalman_filter.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import time

@dataclass
class TrackState:
    pos_ned: np.ndarray   # shape (3,)
    vel_ned: np.ndarray   # shape (3,)
    t: float              # last update time (seconds)

class KalmanCV3D:
    """
    Constant Velocity (CV) Kalman Filter in 3D:
      state x = [N, E, D, vN, vE, vD]^T
      measurement z = [N, E, D]^T
    """
    def __init__(
        self,
        meas_var: float = 25.0,        # measurement variance (m^2). e.g. sigma=5m -> 25
        accel_var: float = 4.0,        # process accel variance (m^2/s^4). tuning
        init_pos_var: float = 100.0,   # initial position uncertainty (m^2)
        init_vel_var: float = 100.0,   # initial velocity uncertainty ((m/s)^2)
    ):
        self.x = np.zeros((6, 1), dtype=float)

        self.P = np.diag([init_pos_var]*3 + [init_vel_var]*3).astype(float)
        self.R = np.eye(3, dtype=float) * meas_var
        self.accel_var = float(accel_var)

        # measurement matrix H maps state -> position
        self.H = np.zeros((3, 6), dtype=float)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0

        self.I = np.eye(6, dtype=float)

    def _F_Q(self, dt: float) -> tuple[np.ndarray, np.ndarray]:
        dt = float(max(1e-3, dt))

        # State transition
        F = np.eye(6, dtype=float)
        F[0, 3] = dt
        F[1, 4] = dt
        F[2, 5] = dt

        # Process noise (white acceleration model)
        # For each axis:
        # Qpospos = dt^4/4 * a_var
        # Qposvel = dt^3/2 * a_var
        # Qvelvel = dt^2   * a_var
        q = self.accel_var
        dt2 = dt*dt
        dt3 = dt2*dt
        dt4 = dt2*dt2

        Q1 = np.array([[dt4/4, dt3/2],
                       [dt3/2, dt2  ]], dtype=float) * q

        Q = np.zeros((6, 6), dtype=float)
        for i, vel_i in [(0, 3), (1, 4), (2, 5)]:
            Q[i, i]       = Q1[0, 0]
            Q[i, vel_i]   = Q1[0, 1]
            Q[vel_i, i]   = Q1[1, 0]
            Q[vel_i, vel_i] = Q1[1, 1]

        return F, Q

    def predict(self, dt: float) -> None:
        F, Q = self._F_Q(dt)
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def update(self, z_pos_ned: np.ndarray) -> None:
        z = np.asarray(z_pos_ned, dtype=float).reshape(3, 1)

        y = z - (self.H @ self.x)                          # innovation
        S = self.H @ self.P @ self.H.T + self.R            # innovation cov
        K = self.P @ self.H.T @ np.linalg.inv(S)           # Kalman gain

        self.x = self.x + K @ y
        self.P = (self.I - K @ self.H) @ self.P

    def set_state_from_measurement(self, z_pos_ned: np.ndarray) -> None:
        z = np.asarray(z_pos_ned, dtype=float).reshape(3, 1)
        self.x[:] = 0.0
        self.x[0:3] = z  # position init, velocity 0

class MultiTargetTracker:
    """
    ID -> Kalman filter map
    """
    def __init__(self, meas_var: float = 25.0, accel_var: float = 4.0, reset_dt: float = 3.0):
        self.meas_var = meas_var
        self.accel_var = accel_var
        self.reset_dt = float(reset_dt)
        self.filters: dict[str, KalmanCV3D] = {}
        self.last_t: dict[str, float] = {}

    def update(self, track_id: str, z_pos_ned: np.ndarray, t: float | None = None) -> TrackState:
        now = time.time() if t is None else float(t)

        if track_id not in self.filters:
            kf = KalmanCV3D(meas_var=self.meas_var, accel_var=self.accel_var)
            kf.set_state_from_measurement(z_pos_ned)
            self.filters[track_id] = kf
            self.last_t[track_id] = now

            x = kf.x.flatten()
            return TrackState(pos_ned=x[0:3].copy(), vel_ned=x[3:6].copy(), t=now)

        kf = self.filters[track_id]
        dt = now - self.last_t[track_id]

        # Çok uzun süre veri gelmediyse resetlemek daha sağlıklı
        if dt > self.reset_dt:
            kf.set_state_from_measurement(z_pos_ned)
            self.last_t[track_id] = now
        else:
            kf.predict(dt)
            kf.update(z_pos_ned)
            self.last_t[track_id] = now

        x = kf.x.flatten()
        return TrackState(pos_ned=x[0:3].copy(), vel_ned=x[3:6].copy(), t=now)
'''