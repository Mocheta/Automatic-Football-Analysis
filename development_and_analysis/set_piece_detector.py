import sys
sys.path.append('../')
from utils import get_center_of_bbox


class SetPieceDetector:
    """Heuristic detector for corners, throw-ins, penalties, and free kicks.

    Strategy: walk through the ball trajectory and find moments where the ball
    has been stationary for ~1.5 s and is then suddenly accelerated (a kick).
    Classify the event by the pixel location where the ball was sitting.

    Known limitations:
    - "Free kick" really means "stoppage in mid-field that is not a throw-in,
      corner, or penalty", so it also catches kickoffs after goals and any
      other unidentified dead-ball moment.
    - Penalty detection assumes a 1920x1080 broadcast view with the standard
      pitch layout; non-standard camera angles will miss penalties or
      misclassify them as free kicks.
    - Throw-ins are detected from where the ball is placed for the throw, not
      from the ball crossing the touchline (interpolation hides that signal).
    """

    def __init__(self, frame_width=1920, frame_height=1080):
        self.events = []
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.stationary_speed_px = 3
        self.kick_speed_px = 25
        self.stationary_min_frames = 18      # ~0.75 s @ 24 fps — catches quickly-taken set pieces
        self.event_debounce_frames = 90

        # Visible-pitch corners in pixels (from view_transformer.pixel_vertices).
        self.corner_radius_px = 160
        self.corners_px = [(265, 275), (910, 260), (1640, 915), (110, 1035)]

        # Approximate penalty-spot zones (pixel coords, 1920x1080 broadcast).
        self.penalty_zones = [
            {'x': (50, 260),   'y': (470, 610)},
            {'x': (1660, 1870), 'y': (470, 610)},
        ]

        # Touchline strips for throw-ins.
        self.throwin_top_y = 280
        self.throwin_bottom_y = 880

    def _ball_positions(self, tracks):
        positions = []
        for frame_data in tracks['ball']:
            if 1 in frame_data and frame_data[1].get('bbox'):
                bbox = frame_data[1]['bbox']
                if any(v != v for v in bbox):
                    positions.append(None)
                else:
                    positions.append(get_center_of_bbox(bbox))
            else:
                positions.append(None)
        return positions

    def _classify_location(self, x, y):
        for cx, cy in self.corners_px:
            if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 < self.corner_radius_px:
                return 'corner', ('left' if cx < self.frame_width / 2 else 'right')

        for zone in self.penalty_zones:
            if zone['x'][0] <= x <= zone['x'][1] and zone['y'][0] <= y <= zone['y'][1]:
                return 'penalty', ('left' if zone['x'][0] < self.frame_width / 2 else 'right')

        if y < self.throwin_top_y or y > self.throwin_bottom_y:
            return 'throw_in', None

        return 'free_kick', None

    def _team_of_kicker(self, tracks, frame_idx, kick_pos):
        if frame_idx >= len(tracks['players']):
            return None
        nearest_team = None
        nearest_dist = float('inf')
        for info in tracks['players'][frame_idx].values():
            bbox = info.get('bbox')
            if not bbox:
                continue
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            d = ((cx - kick_pos[0]) ** 2 + (cy - kick_pos[1]) ** 2) ** 0.5
            if d < nearest_dist:
                nearest_dist = d
                nearest_team = info.get('team')
        return nearest_team

    def detect(self, tracks, camera_movement_per_frame=None):
        positions = self._ball_positions(tracks)
        n = len(positions)

        # Build camera-stabilised ball positions for speed calculation. Without
        # this, a stationary ball appears to move whenever the camera pans.
        if camera_movement_per_frame is not None:
            cum_x = 0.0
            cum_y = 0.0
            stable = []
            for i in range(n):
                if i < len(camera_movement_per_frame):
                    cum_x += camera_movement_per_frame[i][0]
                    cum_y += camera_movement_per_frame[i][1]
                if positions[i] is None:
                    stable.append(None)
                else:
                    stable.append((positions[i][0] - cum_x, positions[i][1] - cum_y))
        else:
            stable = positions

        speeds = [0.0] * n
        for i in range(1, n):
            if stable[i] is None or stable[i - 1] is None:
                continue
            speeds[i] = ((stable[i][0] - stable[i - 1][0]) ** 2 +
                         (stable[i][1] - stable[i - 1][1]) ** 2) ** 0.5

        stationary_start = None
        last_event_frame = -10**9
        for i in range(n):
            is_stationary = positions[i] is not None and speeds[i] <= self.stationary_speed_px

            if is_stationary:
                if stationary_start is None:
                    stationary_start = i
                continue

            if (stationary_start is not None
                    and (i - stationary_start) >= self.stationary_min_frames
                    and speeds[i] >= self.kick_speed_px
                    and (i - last_event_frame) >= self.event_debounce_frames
                    and positions[i] is not None):
                kick_pos = positions[stationary_start]
                event_type, side = self._classify_location(*kick_pos)
                team = self._team_of_kicker(tracks, i, kick_pos)
                self.events.append({
                    'frame': i,
                    'type': event_type,
                    'side': side,
                    'team': team,
                    'ball_position': kick_pos,
                })
                last_event_frame = i

            stationary_start = None

        return self.events

    def get_statistics(self):
        types = ('corner', 'throw_in', 'free_kick', 'penalty')
        counts = {t: 0 for t in types}
        team_counts = {1: dict(counts), 2: dict(counts)}
        for e in self.events:
            t = e['type']
            if t in counts:
                counts[t] += 1
                if e.get('team') in (1, 2):
                    team_counts[e['team']][t] += 1
        return {
            'total_set_pieces': len(self.events),
            'corners': counts['corner'],
            'throw_ins': counts['throw_in'],
            'free_kicks': counts['free_kick'],
            'penalties': counts['penalty'],
            'team_1_corners': team_counts[1]['corner'],
            'team_2_corners': team_counts[2]['corner'],
            'team_1_throw_ins': team_counts[1]['throw_in'],
            'team_2_throw_ins': team_counts[2]['throw_in'],
            'team_1_free_kicks': team_counts[1]['free_kick'],
            'team_2_free_kicks': team_counts[2]['free_kick'],
            'team_1_penalties': team_counts[1]['penalty'],
            'team_2_penalties': team_counts[2]['penalty'],
        }
