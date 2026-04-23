import numpy as np
from sklearn.cluster import KMeans
import sys
sys.path.append('../')


class FormationDetector:
    def __init__(self):
        self.team_formations = {}

    def _get_top_player_positions(self, team_id, tracks):
        player_frame_counts = {}
        player_positions_sum = {}

        for frame_idx in range(len(tracks['players'])):
            for player_id, track_info in tracks['players'][frame_idx].items():
                if track_info.get('team') != team_id:
                    continue
                pos = track_info.get('position_adjusted')
                if pos is None:
                    continue
                if player_id not in player_frame_counts:
                    player_frame_counts[player_id] = 0
                    player_positions_sum[player_id] = [0.0, 0.0]
                player_frame_counts[player_id] += 1
                player_positions_sum[player_id][0] += pos[0]
                player_positions_sum[player_id][1] += pos[1]

        # Average position per player, require at least 5 frame appearances
        avg_positions = {}
        for player_id, count in player_frame_counts.items():
            if count >= 5:
                avg_positions[player_id] = [
                    player_positions_sum[player_id][0] / count,
                    player_positions_sum[player_id][1] / count
                ]

        # Keep only the top 10 most-seen players to avoid track fragmentation
        top_ids = sorted(
            [p for p in player_frame_counts if p in avg_positions],
            key=lambda p: player_frame_counts[p],
            reverse=True
        )[:10]

        return {p: avg_positions[p] for p in top_ids}

    def _detect_formation(self, avg_positions):
        n = len(avg_positions)
        if n < 6:
            return 'Unknown'

        positions_array = np.array(list(avg_positions.values()))

        # Use y-coordinate (vertical pixel axis = depth into pitch in broadcast cameras)
        y_positions = positions_array[:, 1].reshape(-1, 1)

        # 3 clusters for the three outfield lines (defence, midfield, attack)
        n_clusters = min(3, n)
        kmeans = KMeans(n_clusters=n_clusters, init='k-means++', n_init=10, random_state=42)
        kmeans.fit(y_positions)

        sorted_idx = np.argsort(kmeans.cluster_centers_.flatten())
        counts = [int(np.sum(kmeans.labels_ == i)) for i in sorted_idx]

        return '-'.join(map(str, counts))

    def detect_formations(self, tracks):
        for team_id in [1, 2]:
            avg_positions = self._get_top_player_positions(team_id, tracks)
            formation = self._detect_formation(avg_positions)
            self.team_formations[team_id] = formation

        return self.team_formations

    def get_statistics(self):
        return {
            'team_1_formation': self.team_formations.get(1, 'Unknown'),
            'team_2_formation': self.team_formations.get(2, 'Unknown'),
        }
