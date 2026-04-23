import sys
sys.path.append('../')

FRAME_RATE = 24
SPRINT_THRESHOLD_KMH = 25  # high-intensity run threshold

class PassDetector:
    def __init__(self):
        self.passes = []
        self.turnovers = []

    def detect_passes(self, tracks):
        previous_player_with_ball = None
        previous_player_team = None
        previous_frame = None

        for frame_idx in range(len(tracks['players'])):
            player_track = tracks['players'][frame_idx]

            current_player_with_ball = None
            current_player_team = None

            for player_id, track_info in player_track.items():
                if track_info.get('has_ball', False):
                    current_player_with_ball = player_id
                    current_player_team = track_info.get('team', None)
                    break

            if (current_player_with_ball is not None and
                    previous_player_with_ball is not None and
                    current_player_team is not None and
                    previous_player_team is not None and
                    current_player_with_ball != previous_player_with_ball):

                if current_player_team == previous_player_team:
                    self.passes.append({
                        'frame': frame_idx,
                        'from_player': previous_player_with_ball,
                        'to_player': current_player_with_ball,
                        'team': current_player_team,
                        'frame_start': previous_frame,
                        'frame_end': frame_idx,
                    })
                else:
                    self.turnovers.append({
                        'frame': frame_idx,
                        'from_player': previous_player_with_ball,
                        'from_team': previous_player_team,
                        'to_player': current_player_with_ball,
                        'to_team': current_player_team,
                    })

            if current_player_with_ball is not None:
                previous_player_with_ball = current_player_with_ball
                previous_player_team = current_player_team
                previous_frame = frame_idx

        return self.passes

    def add_passes_to_tracks(self, tracks):
        self.detect_passes(tracks)

        for frame_idx in range(len(tracks['players'])):
            for player_id in tracks['players'][frame_idx].keys():
                if 'passes_given' not in tracks['players'][frame_idx][player_id]:
                    tracks['players'][frame_idx][player_id]['passes_given'] = 0
                if 'passes_received' not in tracks['players'][frame_idx][player_id]:
                    tracks['players'][frame_idx][player_id]['passes_received'] = 0

        for pass_info in self.passes:
            from_player = pass_info['from_player']
            to_player = pass_info['to_player']
            frame_end = pass_info['frame_end']

            for frame_idx in range(frame_end, len(tracks['players'])):
                if from_player in tracks['players'][frame_idx]:
                    tracks['players'][frame_idx][from_player]['passes_given'] = \
                        tracks['players'][frame_idx][from_player].get('passes_given', 0) + 1
                if to_player in tracks['players'][frame_idx]:
                    tracks['players'][frame_idx][to_player]['passes_received'] = \
                        tracks['players'][frame_idx][to_player].get('passes_received', 0) + 1

    def get_pass_statistics(self):
        team_1_passes = sum(1 for p in self.passes if p['team'] == 1)
        team_2_passes = sum(1 for p in self.passes if p['team'] == 2)
        team_1_turnovers = sum(1 for t in self.turnovers if t['from_team'] == 1)
        team_2_turnovers = sum(1 for t in self.turnovers if t['from_team'] == 2)

        def accuracy(passes, turnovers):
            total = passes + turnovers
            return (passes / total * 100) if total > 0 else 0.0

        avg_duration = (
            sum(p['frame_end'] - p['frame_start'] for p in self.passes) / len(self.passes)
            if self.passes else 0
        )

        return {
            'total_passes': len(self.passes),
            'team_1_passes': team_1_passes,
            'team_2_passes': team_2_passes,
            'avg_pass_duration': avg_duration,
            'team_1_turnovers': team_1_turnovers,
            'team_2_turnovers': team_2_turnovers,
            'team_1_accuracy': accuracy(team_1_passes, team_1_turnovers),
            'team_2_accuracy': accuracy(team_2_passes, team_2_turnovers),
        }

    def get_player_stats(self, tracks):
        """Aggregate per-player: total distance, top speed, ball possession time."""
        stats = {}

        for frame_idx, player_track in enumerate(tracks['players']):
            for player_id, track_info in player_track.items():
                if player_id not in stats:
                    stats[player_id] = {
                        'team': None,
                        'total_distance': 0.0,
                        'top_speed': 0.0,
                        'possession_frames': 0,
                        'sprint_count': 0,
                    }
                entry = stats[player_id]

                if track_info.get('team') is not None:
                    entry['team'] = track_info['team']

                speed = track_info.get('speed') or 0.0
                distance = track_info.get('distance') or 0.0

                if speed > entry['top_speed']:
                    entry['top_speed'] = speed
                if speed >= SPRINT_THRESHOLD_KMH:
                    entry['sprint_count'] += 1
                # distance is cumulative in tracks — keep the highest value seen
                if distance > entry['total_distance']:
                    entry['total_distance'] = distance

                if track_info.get('has_ball', False):
                    entry['possession_frames'] += 1

        # Drop pure noise detections and keep only the top 11 per team by distance
        filtered = {}
        for team_id in [1, 2]:
            team_players = [
                (pid, s) for pid, s in stats.items()
                if s.get('team') == team_id
                and (s['total_distance'] > 0 or s['possession_frames'] > 0)
            ]
            top11 = sorted(team_players, key=lambda x: x[1]['total_distance'], reverse=True)[:11]
            for pid, s in top11:
                filtered[pid] = s

        return filtered

    def get_team_stats(self, tracks):
        player_stats = self.get_player_stats(tracks)
        result = {}
        for team_id in [1, 2]:
            team = [s for s in player_stats.values() if s.get('team') == team_id]
            result[f'team_{team_id}_total_distance'] = sum(s['total_distance'] for s in team)
            result[f'team_{team_id}_sprints'] = sum(s['sprint_count'] for s in team)
        return result

    def save_stats_to_file(self, filename='output/Stats.txt',
                           formation_detector=None, shot_detector=None,
                           tracks=None, team_ball_control=None):

        pass_stats = self.get_pass_statistics()

        with open(filename, 'w') as f:

            # ── POSSESSION ─────────────────────────────────────────────────────
            f.write("=" * 80 + "\n")
            f.write("FOOTBALL MATCH - BALL POSSESSION\n")
            f.write("=" * 80 + "\n\n")

            if team_ball_control is not None and len(team_ball_control) > 0:
                total = len(team_ball_control)
                t1_pct = (team_ball_control == 1).sum() / total * 100
                t2_pct = (team_ball_control == 2).sum() / total * 100
                f.write(f"Team 1 Possession: {t1_pct:.1f}%\n")
                f.write(f"Team 2 Possession: {t2_pct:.1f}%\n")
            else:
                f.write("Possession data not available.\n")

            f.write("\n")

            # ── FORMATION ANALYSIS ─────────────────────────────────────────────
            f.write("=" * 80 + "\n")
            f.write("FOOTBALL MATCH - FORMATION ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            if formation_detector is not None:
                formation_stats = formation_detector.get_statistics()
                f.write(f"Team 1 Formation: {formation_stats['team_1_formation']}\n")
                f.write(f"Team 2 Formation: {formation_stats['team_2_formation']}\n")
            else:
                f.write("Formation detection was not run.\n")

            f.write("\n")

            # ── SHOT ANALYSIS ──────────────────────────────────────────────────
            f.write("=" * 80 + "\n")
            f.write("FOOTBALL MATCH - SHOT ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            if shot_detector is not None:
                shot_stats = shot_detector.get_statistics()
                f.write(f"Total Shots Detected: {shot_stats['total_shots']}\n\n")
                f.write(f"Team 1 Shots: {shot_stats['team_1_shots']}\n")
                f.write(f"  On Target:  {shot_stats['team_1_on_target']}\n")
                f.write(f"  Off Target: {shot_stats['team_1_off_target']}\n\n")
                f.write(f"Team 2 Shots: {shot_stats['team_2_shots']}\n")
                f.write(f"  On Target:  {shot_stats['team_2_on_target']}\n")
                f.write(f"  Off Target: {shot_stats['team_2_off_target']}\n\n")
                f.write("=" * 80 + "\n\n")

                if shot_detector.shots:
                    for idx, shot_info in enumerate(shot_detector.shots, 1):
                        f.write(f"Shot #{idx}:\n")
                        f.write(f"  Frame:          {shot_info['frame']}\n")
                        f.write(f"  Player ID:      {shot_info['player_id']}\n")
                        f.write(f"  Team:           {shot_info['team']}\n")
                        f.write(f"  Classification: {shot_info['classification'].replace('_', ' ').title()}\n")
                        f.write(f"  Ball Speed:     {shot_info['ball_speed_px']} px/frame\n")
                        f.write("-" * 80 + "\n")
                else:
                    f.write("No shots detected in this match.\n")
            else:
                f.write("Shot detection was not run.\n")

            f.write("\n")

            # ── PASS & TURNOVER ANALYSIS ───────────────────────────────────────
            f.write("=" * 80 + "\n")
            f.write("FOOTBALL MATCH - PASS & TURNOVER ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Total Passes Detected: {pass_stats['total_passes']}\n\n")
            f.write(f"Team 1 Passes:    {pass_stats['team_1_passes']}\n")
            f.write(f"Team 1 Turnovers: {pass_stats['team_1_turnovers']}\n")
            f.write(f"Team 1 Pass Accuracy: {pass_stats['team_1_accuracy']:.1f}%\n\n")
            f.write(f"Team 2 Passes:    {pass_stats['team_2_passes']}\n")
            f.write(f"Team 2 Turnovers: {pass_stats['team_2_turnovers']}\n")
            f.write(f"Team 2 Pass Accuracy: {pass_stats['team_2_accuracy']:.1f}%\n\n")
            f.write(f"Average Pass Duration: {pass_stats['avg_pass_duration']:.1f} frames\n\n")

            if self.passes:
                f.write("=" * 80 + "\n\n")
                for idx, pass_info in enumerate(self.passes, 1):
                    f.write(f"Pass #{idx}:\n")
                    f.write(f"  Frame:          {pass_info['frame']}\n")
                    f.write(f"  From Player ID: {pass_info['from_player']} -> To Player ID: {pass_info['to_player']}\n")
                    f.write(f"  Team:           {pass_info['team']}\n")
                    f.write(f"  Duration:       {pass_info['frame_end'] - pass_info['frame_start']} frames\n")
                    f.write("-" * 80 + "\n")
            else:
                f.write("No passes detected in this match.\n")

            f.write("\n")

            if self.turnovers:
                f.write("=" * 80 + "\n")
                f.write("TURNOVERS / INTERCEPTIONS\n")
                f.write("=" * 80 + "\n\n")
                for idx, t in enumerate(self.turnovers, 1):
                    f.write(f"Turnover #{idx}:\n")
                    f.write(f"  Frame:       {t['frame']}\n")
                    f.write(f"  Lost by:     Player {t['from_player']} (Team {t['from_team']})\n")
                    f.write(f"  Gained by:   Player {t['to_player']} (Team {t['to_team']})\n")
                    f.write("-" * 80 + "\n")
                f.write("\n")

            # ── PLAYER STATS ───────────────────────────────────────────────────
            if tracks is not None:
                f.write("=" * 80 + "\n")
                f.write("FOOTBALL MATCH - PLAYER STATS\n")
                f.write("=" * 80 + "\n\n")

                player_stats = self.get_player_stats(tracks)

                for team_id in [1, 2]:
                    f.write(f"Team {team_id}:\n")
                    f.write(f"  {'Player ID':<12} {'Distance (m)':<16} {'Top Speed (km/h)':<20} {'Possession (s)':<16}\n")
                    f.write(f"  {'-'*64}\n")

                    team_players = {pid: s for pid, s in player_stats.items() if s['team'] == team_id}
                    for player_id, s in sorted(team_players.items()):
                        possession_sec = s['possession_frames'] / FRAME_RATE
                        f.write(f"  {player_id:<12} {s['total_distance']:<16.1f} {s['top_speed']:<20.1f} {possession_sec:<16.1f}\n")

                    f.write("\n")
