import sys
sys.path.append('../')
from utils import get_center_of_bbox, measure_distance


class ShotDetector:
    def __init__(self):
        self.shots = []
        self.ball_speed_threshold = 40          # pixels/frame — high enough to exclude normal passes
        self.max_frames_since_possession = 10   # frames after losing ball to still count as a shot
        self.shot_debounce_frames = 30          # minimum frames between two detected shots
        self.teammate_reception_window = 40     # if a teammate receives within this many frames, it was a pass

        # Goal mouth bounds in pixel coordinates (approximate for 1920x1080 broadcast)
        self.left_goal  = {'x': 0,    'y1': 400, 'y2': 680}
        self.right_goal = {'x': 1920, 'y1': 400, 'y2': 680}

    def _get_ball_positions(self, tracks):
        positions = []
        for frame_data in tracks['ball']:
            if 1 in frame_data and frame_data[1].get('bbox'):
                positions.append(get_center_of_bbox(frame_data[1]['bbox']))
            else:
                positions.append(None)
        return positions

    def _extrapolate_y_at_x(self, p1, p2, target_x):
        dx = p2[0] - p1[0]
        if dx == 0:
            return None
        t = (target_x - p1[0]) / dx
        return p1[1] + t * (p2[1] - p1[1])

    def _classify_shot(self, p1, p2):
        if p1 is None or p2 is None:
            return 'unknown'

        dx = p2[0] - p1[0]

        if dx < -5:
            goal = self.left_goal
        elif dx > 5:
            goal = self.right_goal
        else:
            return 'off_target'

        y = self._extrapolate_y_at_x(p1, p2, goal['x'])
        if y is None:
            return 'off_target'

        return 'on_target' if goal['y1'] <= y <= goal['y2'] else 'off_target'

    def _ball_was_moving_before(self, ball_positions, frame_idx, lookback=3, min_avg_speed=5):
        """Returns True if the ball had consistent movement in the frames before the spike,
        which filters out interpolation artifacts (ball was stationary then jumped)."""
        speeds = []
        for i in range(frame_idx - lookback, frame_idx):
            if i < 1:
                continue
            if ball_positions[i] is not None and ball_positions[i - 1] is not None:
                speeds.append(measure_distance(ball_positions[i], ball_positions[i - 1]))
        if not speeds:
            return False
        return (sum(speeds) / len(speeds)) >= min_avg_speed

    def _teammate_receives_ball(self, tracks, frame_idx, kicker_team, window):
        """Returns True if a player on the same team receives the ball within `window` frames,
        meaning this was a pass, not a shot."""
        end_frame = min(frame_idx + window, len(tracks['players']))
        for f in range(frame_idx + 1, end_frame):
            for player_id, track_info in tracks['players'][f].items():
                if track_info.get('has_ball', False) and track_info.get('team') == kicker_team:
                    return True
        return False

    def detect_shots(self, tracks):
        ball_positions = self._get_ball_positions(tracks)
        number_of_frames = len(tracks['players'])

        last_player_with_ball = None
        last_player_team = None
        frames_since_possession = 0

        for frame_idx in range(1, number_of_frames):
            # Track who currently has the ball
            player_with_ball = None
            player_team = None
            for player_id, track_info in tracks['players'][frame_idx].items():
                if track_info.get('has_ball', False):
                    player_with_ball = player_id
                    player_team = track_info.get('team')
                    break

            if player_with_ball is not None:
                last_player_with_ball = player_with_ball
                last_player_team = player_team
                frames_since_possession = 0
            else:
                frames_since_possession += 1

            p_prev = ball_positions[frame_idx - 1]
            p_curr = ball_positions[frame_idx]

            if p_prev is None or p_curr is None:
                continue

            ball_speed = measure_distance(p_curr, p_prev)

            if not (ball_speed > self.ball_speed_threshold
                    and player_with_ball is None
                    and frames_since_possession <= self.max_frames_since_possession
                    and last_player_with_ball is not None):
                continue

            # Debounce
            if self.shots and (frame_idx - self.shots[-1]['frame']) < self.shot_debounce_frames:
                continue

            # Filter out interpolation artifacts: ball must have been moving before this spike
            if not self._ball_was_moving_before(ball_positions, frame_idx):
                continue

            # Filter out passes: if a teammate receives the ball shortly after, it was a pass
            if self._teammate_receives_ball(tracks, frame_idx, last_player_team, self.teammate_reception_window):
                continue

            classification = self._classify_shot(p_prev, p_curr)

            self.shots.append({
                'frame': frame_idx,
                'player_id': last_player_with_ball,
                'team': last_player_team,
                'ball_speed_px': round(ball_speed, 2),
                'classification': classification,
            })

        return self.shots

    def get_statistics(self):
        if not self.shots:
            return {
                'total_shots': 0,
                'team_1_shots': 0,
                'team_1_on_target': 0,
                'team_1_off_target': 0,
                'team_2_shots': 0,
                'team_2_on_target': 0,
                'team_2_off_target': 0,
            }

        t1 = [s for s in self.shots if s['team'] == 1]
        t2 = [s for s in self.shots if s['team'] == 2]

        return {
            'total_shots': len(self.shots),
            'team_1_shots': len(t1),
            'team_1_on_target':  sum(1 for s in t1 if s['classification'] == 'on_target'),
            'team_1_off_target': sum(1 for s in t1 if s['classification'] == 'off_target'),
            'team_2_shots': len(t2),
            'team_2_on_target':  sum(1 for s in t2 if s['classification'] == 'on_target'),
            'team_2_off_target': sum(1 for s in t2 if s['classification'] == 'off_target'),
        }
