import sys
sys.path.append('../')

class PassDetector:
    def __init__(self):
        self.passes = []
        
    def detect_passes(self, tracks):
        
        previous_player_with_ball = None
        previous_player_team = None
        previous_frame = None
        
        number_of_frames = len(tracks['players'])
        
        for frame_idx in range(number_of_frames):
            player_track = tracks['players'][frame_idx]
            
            current_player_with_ball = None
            current_player_team = None
            
            # Find which player has the ball in current frame
            for player_id, track_info in player_track.items():
                if track_info.get('has_ball', False):
                    current_player_with_ball = player_id
                    current_player_team = track_info.get('team', None)
                    break
            
            # Check if we detected a pass (possession changed between teammates)
            if (current_player_with_ball is not None and 
                previous_player_with_ball is not None and
                current_player_team is not None and
                previous_player_team is not None):
                
                # Different player has the ball
                if current_player_with_ball != previous_player_with_ball:
                    # Only count as pass if both players are on the SAME team
                    if current_player_team == previous_player_team:
                        pass_info = {
                            'frame': frame_idx,
                            'from_player': previous_player_with_ball,
                            'to_player': current_player_with_ball,
                            'team': current_player_team,
                            'frame_start': previous_frame,
                            'frame_end': frame_idx
                        }
                        self.passes.append(pass_info)
            
            # Update previous player tracking
            if current_player_with_ball is not None:
                previous_player_with_ball = current_player_with_ball
                previous_player_team = current_player_team
                previous_frame = frame_idx
        
        return self.passes
    
    def add_passes_to_tracks(self, tracks):
        
        # First, detect all passes
        self.detect_passes(tracks)
        
        # Initialize pass counters for all players
        for frame_idx in range(len(tracks['players'])):
            for player_id in tracks['players'][frame_idx].keys():
                if 'passes_given' not in tracks['players'][frame_idx][player_id]:
                    tracks['players'][frame_idx][player_id]['passes_given'] = 0
                if 'passes_received' not in tracks['players'][frame_idx][player_id]:
                    tracks['players'][frame_idx][player_id]['passes_received'] = 0
        
        # Add pass counts to tracks
        for pass_info in self.passes:
            from_player = pass_info['from_player']
            to_player = pass_info['to_player']
            frame_start = pass_info['frame_start']
            frame_end = pass_info['frame_end']
            
            # Add pass counts to all frames after the pass
            for frame_idx in range(frame_end, len(tracks['players'])):
                if from_player in tracks['players'][frame_idx]:
                    tracks['players'][frame_idx][from_player]['passes_given'] = \
                        tracks['players'][frame_idx][from_player].get('passes_given', 0) + 1
                
                if to_player in tracks['players'][frame_idx]:
                    tracks['players'][frame_idx][to_player]['passes_received'] = \
                        tracks['players'][frame_idx][to_player].get('passes_received', 0) + 1
    
    def get_pass_statistics(self):
        
        if not self.passes:
            return {
                'total_passes': 0,
                'team_1_passes': 0,
                'team_2_passes': 0,
                'avg_pass_duration': 0
            }
        
        team_1_passes = sum(1 for p in self.passes if p['team'] == 1)
        team_2_passes = sum(1 for p in self.passes if p['team'] == 2)
        avg_duration = sum(p['frame_end'] - p['frame_start'] for p in self.passes) / len(self.passes)
        
        return {
            'total_passes': len(self.passes),
            'team_1_passes': team_1_passes,
            'team_2_passes': team_2_passes,
            'avg_pass_duration': avg_duration
        }
    
    def save_passes_to_file(self, filename='development_and_analysis/passes.txt'):
        
        stats = self.get_pass_statistics()
        
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("FOOTBALL MATCH - PASS ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            
            if not self.passes:
                f.write("No passes detected in this match.\n")
                return
            
            f.write(f"Total Passes Detected: {stats['total_passes']}\n\n")
            f.write(f"Team 1 Passes: {stats['team_1_passes']}\n")
            f.write(f"Team 2 Passes: {stats['team_2_passes']}\n\n")
            f.write(f"Average Pass Duration: {stats['avg_pass_duration']:.1f} frames\n\n")
            f.write("=" * 80 + "\n\n")
            
            # Write individual passes
            for idx, pass_info in enumerate(self.passes, 1):
                f.write(f"Pass #{idx}:\n")
                f.write(f"  Frame: {pass_info['frame']}\n")
                f.write(f"  From Player ID: {pass_info['from_player']} -> To Player ID: {pass_info['to_player']}\n")
                f.write(f"  Team: {pass_info['team']}\n")
                f.write(f"  Duration: {pass_info['frame_end'] - pass_info['frame_start']} frames\n")
                f.write("-" * 80 + "\n")
        
        