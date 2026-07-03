import sys
sys.path.append('..')
from utils import  get_center_of_bbox, measure_distance

class PlayerBallAssigner:
    def __init__(self):
        self.max_ball_player_distance = 60

    def assign_ball_to_player(self, players, ball_bbox):
        ball_position = get_center_of_bbox(ball_bbox)

        min_distance = 99999
        second_min_distance = 99999
        assigned_player = -1

        for player_id, player in players.items():
            player_bbox = player['bbox']

            distance_left = measure_distance((player_bbox[0], player_bbox[1]), ball_position)
            distance_right = measure_distance((player_bbox[2], player_bbox[1]), ball_position)

            distance = min(distance_left, distance_right)

            if distance < min_distance:
                second_min_distance = min_distance
                if distance < self.max_ball_player_distance:
                    assigned_player = player_id
                min_distance = distance
            elif distance < second_min_distance:
                second_min_distance = distance

        if assigned_player == -1:
            return -1, 0.0

        # Closer = more confident; saturates fully when within 15px of the player.
        if min_distance <= 15:
            closeness_conf = 1.0
        else:
            closeness_conf = max(0.0, 1.0 - (min_distance - 15) / (self.max_ball_player_distance - 15))

        # A clear gap to the second-closest player rules out tug-of-war ambiguity.
        if second_min_distance >= 99999:
            gap_conf = 1.0
        else:
            gap_conf = min(1.0, max(0.0, (second_min_distance - min_distance) / 25.0))

        confidence = 0.7 * closeness_conf + 0.3 * gap_conf
        return assigned_player, confidence