from utils import read_video, save_video
from track import Tracker
import cv2
import numpy as np
from team_assigner import TeamAssigner
from player_ball_assigner import PlayerBallAssigner
from camera_movement import CameraMovement
from view_transformer import ViewTransformer
from development_and_analysis import SpeedAndDistance_Detector, PassDetector

def main():
    # Read video
    video_frames = read_video('VideoData/test+pase.mp4')

    # Initialize tracker
    tracker = Tracker('models/bestm.pt')

    tracks = tracker.get_object_tracks(video_frames, read_from_stub=True, stub_path='stubs/testpase_stub.pkl')

    # Get positions
    tracker.add_position_to_track(tracks)

    # Adjust for camera movement
    camera_movement_detector = CameraMovement(video_frames[0])
    camera_movement_per_frame = camera_movement_detector.get_camera_movement(video_frames, 
                                                                    read_from_stub=True, 
                                                                    stub_path='stubs/testpase_camera_movement_stub.pkl')
    camera_movement_detector.add_adjust_position_to_tracks(tracks, camera_movement_per_frame)

    # Transform to top-down view
    view_transformer = ViewTransformer()
    view_transformer.add_transformed_position_to_tracks(tracks)

    # Interpolate ball positions
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

    # Calculate speed and distance
    speed_and_distance_detector = SpeedAndDistance_Detector()
    speed_and_distance_detector.add_speed_and_distance_to_tracks(tracks)

    # Assign teams and ball possession
    team_assigner = TeamAssigner()
    team_assigner.assign_team_colors(video_frames[0], tracks['players'][0])

    for frame_idx, player_track in enumerate(tracks['players']):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(video_frames[frame_idx], track['bbox'], player_id)
            tracks['players'][frame_idx][player_id]['team'] = team
            tracks['players'][frame_idx][player_id]['team_color'] = team_assigner.team_colors[team]

    player_assigner = PlayerBallAssigner()
    team_ball_control = []
    for frame_idx, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_idx][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

        if assigned_player != -1:
            tracks['players'][frame_idx][assigned_player]['has_ball'] = True
            team_ball_control.append(tracks['players'][frame_idx][assigned_player]['team'])
        else:
            if len(team_ball_control) > 0:
                team_ball_control.append(team_ball_control[-1])
            else:
                team_ball_control.append(1)

    team_ball_control = np.array(team_ball_control)

    # Detect passes and add to tracks
    pass_detector = PassDetector()
    pass_detector.detect_passes(tracks)
    pass_detector.save_passes_to_file('output/passes.txt')

    # Output
    speed_and_distance_detector.draw_speed_and_distance(video_frames, tracks)

    output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)

    save_video(output_video_frames, 'output/outputpase_video.mp4')

if __name__ == "__main__":
    main()